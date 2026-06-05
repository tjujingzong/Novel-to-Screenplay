"""API routes for the novel-to-screenplay converter."""

import asyncio
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response, StreamingResponse

from app.config import get_settings
from app.dependencies import templates
from app.models.enums import ConversionStage
from app.models.requests import ConversionStatus, UploadResponse
from app.models.screenplay import Metadata
from app.services import (
    assembler,
    character_extractor,
    chapter_splitter,
    converter,
    file_parser,
    validator,
    yaml_exporter,
)
from app.services.llm_client import DeepSeekClient

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory job store
_jobs: dict[str, dict] = {}


def _get_job(job_id: str) -> dict:
    """Get job data or raise 404."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _jobs[job_id]


def _update_status(job_id: str, stage: ConversionStage, **kwargs):
    """Update job status."""
    if job_id in _jobs:
        _jobs[job_id]["status"] = ConversionStatus(
            job_id=job_id,
            stage=stage.value,
            **kwargs,
        )


# ─── Pages ───────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the upload/conversion page."""
    return templates.TemplateResponse(request, "index.html")


@router.get("/preview/{job_id}", response_class=HTMLResponse)
async def preview_page(request: Request, job_id: str):
    """Render the YAML preview page."""
    _get_job(job_id)  # Validate job exists
    return templates.TemplateResponse(request, "preview.html", context={"job_id": job_id})


# ─── API Endpoints ───────────────────────────────────────────────────────────

@router.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile):
    """Upload a novel file for conversion."""
    settings = get_settings()

    # Validate file type
    try:
        file_type = file_parser.detect_file_type(file.filename or "unknown.txt")
    except file_parser.FileParsingError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Read and store file
    content = await file.read()
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.max_upload_size_mb}MB)")

    job_id = str(uuid.uuid4())
    upload_path = settings.upload_dir / f"{job_id}_{file.filename}"
    upload_path.write_bytes(content)

    # Extract text for word count
    try:
        text = file_parser.extract_text(upload_path, file_type)
        word_count = file_parser.count_words(text)
    except file_parser.FileParsingError as e:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))

    _jobs[job_id] = {
        "file_path": str(upload_path),
        "file_type": file_type,
        "text": text,
        "status": ConversionStatus(job_id=job_id, stage=ConversionStage.UPLOADED.value),
        "yaml_content": None,
        "validation_issues": [],
    }

    return UploadResponse(
        job_id=job_id,
        filename=file.filename or "unknown",
        file_type=file_type,
        word_count=word_count,
    )


@router.post("/api/convert/{job_id}")
async def start_conversion(job_id: str, background_tasks: BackgroundTasks):
    """Start the conversion process as a background task."""
    job = _get_job(job_id)

    if job["status"].stage == ConversionStage.CONVERTING.value:
        raise HTTPException(status_code=400, detail="Conversion already started")

    background_tasks.add_task(_run_conversion, job_id)

    return {"message": "Conversion started", "job_id": job_id}


@router.get("/api/status/{job_id}")
async def get_status_sse(job_id: str):
    """Stream conversion status via Server-Sent Events."""
    _get_job(job_id)

    async def event_generator():
        while True:
            if job_id not in _jobs:
                break

            status = _jobs[job_id]["status"]
            data = status.model_dump_json()
            yield f"data: {data}\n\n"

            if status.stage in (ConversionStage.COMPLETE.value, ConversionStage.ERROR.value):
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/status/{job_id}/json")
async def get_status_json(job_id: str):
    """Get conversion status as JSON (fallback for non-SSE clients)."""
    job = _get_job(job_id)
    return job["status"]


@router.get("/api/result/{job_id}")
async def download_result(job_id: str):
    """Download the generated YAML screenplay."""
    job = _get_job(job_id)

    if job["status"].stage != ConversionStage.COMPLETE.value:
        raise HTTPException(status_code=400, detail="Conversion not yet complete")

    yaml_content = job.get("yaml_content", "")
    if not yaml_content:
        raise HTTPException(status_code=404, detail="No result available")

    return Response(
        content=yaml_content,
        media_type="text/yaml",
        headers={"Content-Disposition": f"attachment; filename=screenplay_{job_id[:8]}.yaml"},
    )


@router.get("/api/result/{job_id}/text")
async def get_result_text(job_id: str):
    """Get the YAML content as plain text (for preview)."""
    job = _get_job(job_id)

    if job["status"].stage != ConversionStage.COMPLETE.value:
        raise HTTPException(status_code=400, detail="Conversion not yet complete")

    return Response(
        content=job.get("yaml_content", ""),
        media_type="text/plain; charset=utf-8",
    )


@router.get("/api/validate/{job_id}")
async def get_validation(job_id: str):
    """Get validation issues for the completed conversion."""
    job = _get_job(job_id)
    return {"issues": job.get("validation_issues", [])}


# ─── Background Conversion Pipeline ─────────────────────────────────────────

async def _run_conversion(job_id: str):
    """Run the full conversion pipeline as a background task."""
    try:
        await _do_conversion(job_id)
    except Exception as e:
        logger.exception("Conversion failed for job %s", job_id)
        _update_status(job_id, ConversionStage.ERROR, error_message=str(e))


async def _do_conversion(job_id: str):
    """Execute the conversion pipeline."""
    job = _jobs[job_id]
    text = job["text"]

    # Step 1: Parse (already done during upload, but update status)
    _update_status(job_id, ConversionStage.PARSING, progress_percent=5)
    await asyncio.sleep(0.1)

    # Step 2: Split chapters
    _update_status(job_id, ConversionStage.SPLITTING, progress_percent=10)
    chapters = chapter_splitter.split_chapters(text)
    total_chapters = len(chapters)
    _update_status(
        job_id, ConversionStage.SPLITTING,
        progress_percent=15, total_chapters=total_chapters,
    )
    await asyncio.sleep(0.1)

    # Step 3: Extract characters
    _update_status(
        job_id, ConversionStage.EXTRACTING_CHARACTERS,
        progress_percent=20, total_chapters=total_chapters,
    )

    client = DeepSeekClient()
    try:
        characters = await character_extractor.extract_characters(chapters, client)

        # Step 4: Convert each chapter
        _update_status(
            job_id, ConversionStage.CONVERTING,
            progress_percent=30, total_chapters=total_chapters, current_chapter=1,
        )

        context = converter.ConversionContext()
        character_catalog_str = converter.format_character_catalog(characters)
        conversion_results = []

        for i, chapter in enumerate(chapters):
            context.act_number = i + 1

            _update_status(
                job_id, ConversionStage.CONVERTING,
                progress_percent=30 + (50 * (i + 1) / total_chapters),
                total_chapters=total_chapters,
                current_chapter=i + 1,
            )

            result = await converter.convert_chapter(
                chapter=chapter,
                character_catalog_str=character_catalog_str,
                context=context,
                client=client,
            )
            conversion_results.append(result)

        # Step 5: Assemble
        _update_status(
            job_id, ConversionStage.ASSEMBLING,
            progress_percent=85, total_chapters=total_chapters,
        )

        metadata = Metadata(
            title="Adapted Screenplay",
            author="Unknown",
            genre="drama",
            language="zh",
        )

        screenplay = assembler.assemble_screenplay(metadata, characters, conversion_results)

        # Step 6: Validate
        _update_status(
            job_id, ConversionStage.VALIDATING,
            progress_percent=92, total_chapters=total_chapters,
        )

        issues = validator.validate_screenplay(screenplay)
        job["validation_issues"] = [i.model_dump() for i in issues]

        # Step 7: Export YAML
        yaml_content = yaml_exporter.export_to_yaml(screenplay)
        job["yaml_content"] = yaml_content

        # Save to output file
        settings = get_settings()
        output_path = settings.output_dir / f"{job_id}.yaml"
        output_path.write_text(yaml_content, encoding="utf-8")

        _update_status(job_id, ConversionStage.COMPLETE, progress_percent=100)

    finally:
        await client.close()
