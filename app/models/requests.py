"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response after a file is uploaded."""
    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="Detected file type")
    word_count: int = Field(default=0, description="Estimated word count")


class ConversionStatus(BaseModel):
    """Current status of a conversion job."""
    job_id: str
    stage: str = Field(..., description="Current pipeline stage")
    progress_percent: float = Field(default=0.0, description="0-100 progress")
    current_chapter: int | None = Field(default=None, description="Currently converting chapter number")
    total_chapters: int | None = Field(default=None, description="Total chapters detected")
    error_message: str | None = Field(default=None, description="Error detail if stage=error")


class ValidationIssue(BaseModel):
    """A validation warning or error."""
    severity: str = Field(..., description="warning | error")
    path: str = Field(..., description="JSONPath-like location, e.g. 'structure.acts[0].scenes[2]'")
    message: str = Field(..., description="Description of the issue")


class ConversionResult(BaseModel):
    """The completed conversion output."""
    job_id: str
    yaml_content: str = Field(..., description="Generated YAML screenplay")
    validation_issues: list[ValidationIssue] = Field(default_factory=list)


class ConvertRequest(BaseModel):
    """Request body for starting a conversion."""
    api_key: str = Field(default="", description="User-provided DeepSeek API Key")


class YamlEditRequest(BaseModel):
    """Request body for saving edited YAML."""
    yaml_content: str = Field(..., description="Edited YAML content")


class RegenerateRequest(BaseModel):
    """Request body for regenerating YAML with user suggestions."""
    suggestions: str = Field(..., description="User's suggestions/feedback for regeneration")
    api_key: str = Field(default="", description="User-provided DeepSeek API Key")


class ScreenplayEditRequest(BaseModel):
    """Request body for saving edited screenplay."""
    screenplay_content: str = Field(..., description="Edited screenplay content")
