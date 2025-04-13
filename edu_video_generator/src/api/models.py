from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled" # Added cancelled status


class VideoRequest(BaseModel):
    topic: str = Field(..., description="The topic for the educational video")
    language: str = Field("en-US", description="TTS language code (e.g., en-US, hi-IN)")
    voice: Optional[str] = Field(None, description="Specific TTS voice name")
    cleanup: bool = Field(False, description="Clean up intermediate files after completion")
    skip_content_cache: bool = Field(False, description="Force regeneration of content")
    no_animation_cache: bool = Field(False, description="Disable caching of animations")
    
    class Config:
        schema_extra = {
            "example": {
                "topic": "Photosynthesis",
                "language": "en-US",
                "voice": "af_heart",
                "cleanup": False,
                "skip_content_cache": False,
                "no_animation_cache": False
            }
        }


class JobResponse(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the job")
    status: JobStatus = Field(..., description="Current status of the job")
    created_at: str = Field(..., description="Timestamp when job was created")
    topic: str = Field(..., description="Topic of the video")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "f58d7a6c-e1c2-4a7b-b1e4-d6a2bf2e7e9a",
                "status": "processing",
                "created_at": "2025-04-13T09:30:00",
                "topic": "Photosynthesis",
                "estimated_completion": "2025-04-13T09:45:00",
                "progress": 35.0
            }
        }


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class LanguageVoice(BaseModel):
    language_code: str
    language_name: str
    voices: List[Dict[str, str]]  # List of voice IDs and names


class SupportedLanguagesResponse(BaseModel):
    languages: List[LanguageVoice]
