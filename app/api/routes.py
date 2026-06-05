"""API routes for the novel-to-screenplay converter."""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response, StreamingResponse

from app.config import get_settings
from app.dependencies import templates
from app.models.enums import ConversionStage
from app.models.requests import (
    ConversionStatus,
    ConvertRequest,
    RegenerateRequest,
    ScreenplayEditRequest,
    UploadResponse,
    YamlEditRequest,
)
from app.models.screenplay import Metadata
from app.prompts import regeneration as regen_prompts
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
    """Render the YAML preview/editor page."""
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
        "screenplay_content": None,
        "validation_issues": [],
        "original_filename": file.filename or "unknown",
        "created_at": __import__('datetime').datetime.now().isoformat(),
        "stream_buffer": [],
    }

    return UploadResponse(
        job_id=job_id,
        filename=file.filename or "unknown",
        file_type=file_type,
        word_count=word_count,
    )


@router.post("/api/convert/{job_id}")
async def start_conversion(job_id: str, body: ConvertRequest, background_tasks: BackgroundTasks):
    """Start the conversion process as a background task."""
    job = _get_job(job_id)

    if job["status"].stage == ConversionStage.CONVERTING.value:
        raise HTTPException(status_code=400, detail="Conversion already started")

    # Store user-provided API key in job data
    if body.api_key:
        job["api_key"] = body.api_key

    # Reset stream buffer
    job["stream_buffer"] = []

    background_tasks.add_task(_run_conversion, job_id)

    return {"message": "Conversion started", "job_id": job_id}


@router.get("/api/status/{job_id}")
async def get_status_sse(job_id: str):
    """Stream conversion status and LLM output via Server-Sent Events."""
    _get_job(job_id)

    async def event_generator():
        last_chunk_count = 0
        while True:
            if job_id not in _jobs:
                break

            job = _jobs[job_id]
            status = job["status"]

            # Send status update
            status_data = status.model_dump_json()
            yield f"event: status\ndata: {status_data}\n\n"

            # Send any new stream chunks
            chunks = job.get("stream_buffer", [])
            if len(chunks) > last_chunk_count:
                new_chunks = chunks[last_chunk_count:]
                chunk_text = "".join(new_chunks)
                chunk_data = json.dumps({"text": chunk_text}, ensure_ascii=False)
                yield f"event: chunk\ndata: {chunk_data}\n\n"
                last_chunk_count = len(chunks)

            if status.stage in (ConversionStage.COMPLETE.value, ConversionStage.ERROR.value):
                yield f"event: done\ndata: {{}}\n\n"
                break

            await asyncio.sleep(0.5)

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
    """Get the YAML content as plain text (for preview/editor)."""
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


# ─── YAML Editor APIs ───────────────────────────────────────────────────────

@router.put("/api/yaml/{job_id}")
async def save_yaml(job_id: str, body: YamlEditRequest):
    """Save edited YAML content."""
    job = _get_job(job_id)
    job["yaml_content"] = body.yaml_content

    # Save to output file
    settings = get_settings()
    output_path = settings.output_dir / f"{job_id}.yaml"
    output_path.write_text(body.yaml_content, encoding="utf-8")

    return {"message": "YAML saved successfully"}


# ─── Regenerate with Suggestions ─────────────────────────────────────────────

@router.post("/api/regenerate/{job_id}")
async def regenerate_yaml(job_id: str, body: RegenerateRequest):
    """Regenerate YAML based on user suggestions, streaming the result."""
    job = _get_job(job_id)
    current_yaml = job.get("yaml_content", "")

    if not current_yaml:
        raise HTTPException(status_code=400, detail="No YAML content to regenerate")

    async def stream_generator():
        client = DeepSeekClient(api_key=body.api_key or job.get("api_key") or None)
        try:
            user_prompt = regen_prompts.REGENERATE_USER_PROMPT_TEMPLATE.format(
                yaml_content=current_yaml,
                suggestions=body.suggestions,
            )

            stream_result, chunk_gen = await client.complete_stream(
                system_prompt=regen_prompts.REGENERATE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            async for chunk in chunk_gen:
                data = json.dumps({"text": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # Save the regenerated YAML
            new_yaml = stream_result.full_text
            # Strip markdown code fences if present
            new_yaml = _strip_code_fences(new_yaml)
            job["yaml_content"] = new_yaml

            # Save to file
            settings = get_settings()
            output_path = settings.output_dir / f"{job_id}.yaml"
            output_path.write_text(new_yaml, encoding="utf-8")

            yield f"event: done\ndata: {{}}\n\n"

        except Exception as e:
            logger.exception("Regeneration failed for job %s", job_id)
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"
        finally:
            await client.close()

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── YAML to Screenplay ─────────────────────────────────────────────────────

@router.post("/api/screenplay/{job_id}")
async def convert_to_screenplay(job_id: str, body: RegenerateRequest):
    """Convert YAML to formatted screenplay, streaming the result."""
    job = _get_job(job_id)
    current_yaml = job.get("yaml_content", "")

    if not current_yaml:
        raise HTTPException(status_code=400, detail="No YAML content to convert")

    async def stream_generator():
        client = DeepSeekClient(api_key=body.api_key or job.get("api_key") or None)
        try:
            user_prompt = regen_prompts.SCREENPLAY_FORMAT_USER_PROMPT_TEMPLATE.format(
                yaml_content=current_yaml,
            )

            stream_result, chunk_gen = await client.complete_stream(
                system_prompt=regen_prompts.SCREENPLAY_FORMAT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            async for chunk in chunk_gen:
                data = json.dumps({"text": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # Save the screenplay
            screenplay_text = stream_result.full_text
            job["screenplay_content"] = screenplay_text

            # Save to file
            settings = get_settings()
            output_path = settings.output_dir / f"{job_id}.screenplay.txt"
            output_path.write_text(screenplay_text, encoding="utf-8")

            yield f"event: done\ndata: {{}}\n\n"

        except Exception as e:
            logger.exception("Screenplay conversion failed for job %s", job_id)
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"
        finally:
            await client.close()

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/screenplay/{job_id}")
async def get_screenplay(job_id: str):
    """Get the screenplay content."""
    job = _get_job(job_id)
    content = job.get("screenplay_content")
    if not content:
        # Try loading from file
        settings = get_settings()
        output_path = settings.output_dir / f"{job_id}.screenplay.txt"
        if output_path.exists():
            content = output_path.read_text(encoding="utf-8")
            job["screenplay_content"] = content
        else:
            raise HTTPException(status_code=404, detail="No screenplay content available")
    return {"content": content}


@router.put("/api/screenplay/{job_id}")
async def save_screenplay(job_id: str, body: ScreenplayEditRequest):
    """Save edited screenplay content."""
    job = _get_job(job_id)
    job["screenplay_content"] = body.screenplay_content

    # Save to file
    settings = get_settings()
    output_path = settings.output_dir / f"{job_id}.screenplay.txt"
    output_path.write_text(body.screenplay_content, encoding="utf-8")

    return {"message": "Screenplay saved successfully"}


@router.get("/api/screenplay/{job_id}/download")
async def download_screenplay(job_id: str):
    """Download the screenplay as a text file."""
    job = _get_job(job_id)
    content = job.get("screenplay_content", "")
    if not content:
        raise HTTPException(status_code=404, detail="No screenplay content available")

    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=screenplay_{job_id[:8]}.txt"},
    )


# ─── Samples & History ───────────────────────────────────────────────────────

@router.get("/api/samples")
async def list_samples():
    """List available sample novels."""
    settings = get_settings()
    samples_dir = settings.data_dir / "samples"

    if not samples_dir.exists():
        return {"samples": []}

    samples = []
    for f in sorted(samples_dir.iterdir()):
        if f.is_file() and f.suffix in (".txt", ".md"):
            # Extract title from filename (e.g., sample1_月光下的秘密.md -> 月光下的秘密)
            parts = f.stem.split("_", 1)
            title = parts[1] if len(parts) > 1 else f.stem

            # Read first few lines to get a preview
            try:
                content = f.read_text(encoding="utf-8")
                preview = content[:300] + "..." if len(content) > 300 else content
                word_count = len(content)
            except Exception:
                preview = "无法读取预览"
                word_count = 0

            samples.append({
                "id": f.stem,
                "title": title,
                "filename": f.name,
                "preview": preview,
                "word_count": word_count,
            })

    return {"samples": samples}


@router.get("/api/samples/{sample_id}")
async def get_sample(sample_id: str):
    """Get the content of a specific sample."""
    settings = get_settings()
    samples_dir = settings.data_dir / "samples"

    # Find the file
    for ext in (".txt", ".md"):
        file_path = samples_dir / f"{sample_id}{ext}"
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            parts = file_path.stem.split("_", 1)
            title = parts[1] if len(parts) > 1 else file_path.stem
            return {
                "id": sample_id,
                "title": title,
                "content": content,
            }

    raise HTTPException(status_code=404, detail="Sample not found")


@router.get("/api/history")
async def get_history():
    """Get conversion history (in-memory)."""
    history = []
    for job_id, job in _jobs.items():
        status = job.get("status")
        if status:
            history.append({
                "job_id": job_id,
                "stage": status.stage,
                "progress_percent": status.progress_percent,
                "total_chapters": status.total_chapters,
                "error_message": status.error_message,
                "filename": job.get("original_filename", "Unknown"),
                "created_at": job.get("created_at"),
            })

    # Sort by created_at descending (newest first)
    history.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return {"history": history}


# ─── Utilities ───────────────────────────────────────────────────────────────

def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences from text."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```yaml or ```)
        lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text


# ─── Background Conversion Pipeline ─────────────────────────────────────────

async def _run_conversion(job_id: str):
    """Run the full conversion pipeline as a background task."""
    try:
        await _do_conversion(job_id)
    except Exception as e:
        logger.exception("Conversion failed for job %s", job_id)
        _update_status(job_id, ConversionStage.ERROR, error_message=str(e))


async def _do_conversion(job_id: str):
    """Execute the conversion pipeline with streaming support."""
    job = _jobs[job_id]
    text = job["text"]

    # Helper to append stream chunks
    async def append_chunk(chunk: str):
        job["stream_buffer"].append(chunk)

    # Step 1: Parse (already done during upload, but update status)
    _update_status(job_id, ConversionStage.PARSING, progress_percent=5)
    job["stream_buffer"].append("📄 正在解析文件内容...\n")
    await asyncio.sleep(0.1)

    # Step 2: Split chapters
    _update_status(job_id, ConversionStage.SPLITTING, progress_percent=10)
    chapters = chapter_splitter.split_chapters(text)
    total_chapters = len(chapters)
    _update_status(
        job_id, ConversionStage.SPLITTING,
        progress_percent=15, total_chapters=total_chapters,
    )
    job["stream_buffer"].append(f"📑 检测到 {total_chapters} 个章节\n")
    for i, ch in enumerate(chapters):
        job["stream_buffer"].append(f"  • 第{i+1}章: {ch.title or f'段落{i+1}'}\n")
    await asyncio.sleep(0.1)

    # Step 3: Extract characters
    _update_status(
        job_id, ConversionStage.EXTRACTING_CHARACTERS,
        progress_percent=20, total_chapters=total_chapters,
    )
    job["stream_buffer"].append("\n👤 正在提取角色信息...\n")

    client = DeepSeekClient(api_key=job.get("api_key") or None)
    try:
        characters = await character_extractor.extract_characters(chapters, client)
        job["stream_buffer"].append(f"  ✅ 提取到 {len(characters)} 个角色\n")
        for char in characters:
            job["stream_buffer"].append(f"  • {char.name} ({char.role}) — {char.description[:50]}\n")

        # Step 4: Convert each chapter with streaming
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

            job["stream_buffer"].append(f"\n🎬 正在转换第 {i+1}/{total_chapters} 章: {chapter.title or f'段落{i+1}'}\n")
            job["stream_buffer"].append("─" * 40 + "\n")

            result = await converter.convert_chapter(
                chapter=chapter,
                character_catalog_str=character_catalog_str,
                context=context,
                client=client,
                stream_callback=append_chunk,
            )
            conversion_results.append(result)

            job["stream_buffer"].append(f"\n✅ 第 {i+1} 章转换完成\n")

        # Step 5: Assemble
        _update_status(
            job_id, ConversionStage.ASSEMBLING,
            progress_percent=85, total_chapters=total_chapters,
        )
        job["stream_buffer"].append("\n🔧 正在组装完整剧本...\n")

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
        job["stream_buffer"].append("🔍 正在验证剧本...\n")

        issues = validator.validate_screenplay(screenplay)
        job["validation_issues"] = [i.model_dump() for i in issues]

        # Step 7: Export YAML
        yaml_content = yaml_exporter.export_to_yaml(screenplay)
        job["yaml_content"] = yaml_content

        # Save to output file
        settings = get_settings()
        output_path = settings.output_dir / f"{job_id}.yaml"
        output_path.write_text(yaml_content, encoding="utf-8")

        job["stream_buffer"].append(f"✅ 剧本生成完成！共 {total_chapters} 章，{len(characters)} 个角色\n")

        _update_status(job_id, ConversionStage.COMPLETE, progress_percent=100)

    finally:
        await client.close()
