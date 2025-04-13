import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Response # Import Response
from fastapi.responses import FileResponse, JSONResponse
from starlette.status import HTTP_404_NOT_FOUND, HTTP_202_ACCEPTED, HTTP_200_OK # Import HTTP_200_OK

from .models import VideoRequest, JobResponse, JobStatus, SupportedLanguagesResponse, LanguageVoice
from .service import (
    create_job, get_job_data, cancel_job, # Added cancel_job
    SUPPORTED_VOICES, LANGUAGE_CODE_MAP
)

router = APIRouter(prefix="/api/v1")

# Update responses documentation for the endpoint
@router.post(
    "/generate_video/", 
    response_model=JobResponse, 
    responses={
        HTTP_202_ACCEPTED: {"description": "New job successfully queued."},
        HTTP_200_OK: {"description": "Request matched a completed job in cache."},
        429: {"description": "Resource limits exceeded."},
        503: {"description": "Job tracking service unavailable."}
    }
)
async def generate_video(request: VideoRequest, response: Response): # Add Response parameter
    """
    Submit a request to generate an educational video or retrieve a cached result.

    - If the exact request (topic, language, voice) has been successfully completed recently,
      details of the cached job are returned with a **200 OK** status.
    - Otherwise, a new job is queued, and its details are returned with a **202 Accepted** status.
    
    The video generation happens asynchronously for new jobs. Use the returned job_id to check status.
    """
    try:
        # create_job now returns (job_data, is_cached)
        job_data, is_cached = create_job(request.dict())

        # Set status code based on whether it was cached
        if is_cached:
            response.status_code = HTTP_200_OK
        else:
            response.status_code = HTTP_202_ACCEPTED # Default is 202, but set explicitly

        # Return the job data
        return JobResponse(
            job_id=job_data["job_id"],
            status=JobStatus(job_data["status"]), # Status will be 'completed' if cached
            created_at=job_data["created_at"],
            topic=job_data["topic"],
            estimated_completion=job_data.get("estimated_completion"),
            progress=job_data.get("progress", 0.0)
        )
    except HTTPException as e:
        # Re-raise existing HTTP exceptions
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str = Path(..., description="The ID of the job to check")):
    """
    Check the status of a video generation job.
    """
    job_data = get_job_data(job_id)
    if not job_data:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    return JobResponse(
        job_id=job_data["job_id"],
        status=JobStatus(job_data["status"]),
        created_at=job_data["created_at"],
        topic=job_data["topic"],
        estimated_completion=job_data.get("estimated_completion"),
        progress=job_data.get("progress", 0.0)
    )


@router.get("/video/{job_id}", response_class=FileResponse)
async def get_video(job_id: str = Path(..., description="The ID of the job to download video for")):
    """
    Download the generated video for a completed job.
    """
    job_data = get_job_data(job_id)
    if not job_data:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    if job_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Video is not ready. Current status: {job_data['status']}"
        )
    
    output_path = job_data.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Video file not found or was removed"
        )
    
    topic_slug = job_data["topic"].replace(" ", "_").lower()
    filename = f"{topic_slug}_{job_id}.mp4"
    
    return FileResponse(
        path=output_path,
        filename=filename,
        media_type="video/mp4"
    )


@router.get("/languages", response_model=SupportedLanguagesResponse)
async def get_supported_languages():
    """
    Get a list of all supported languages and voices.
    """
    language_mapping = {
        'en-US': 'American English',
        'en-GB': 'British English',
        'es-ES': 'Spanish',
        'fr-FR': 'French',
        'hi-IN': 'Hindi',
        'it-IT': 'Italian',
        'ja-JP': 'Japanese',
        'pt-BR': 'Brazilian Portuguese',
        'zh-CN': 'Mandarin Chinese'
    }
    
    languages = []
    for lang_code, lang_name in language_mapping.items():
        kokoro_code = LANGUAGE_CODE_MAP.get(lang_code)
        if kokoro_code and kokoro_code in SUPPORTED_VOICES:
            voice_data = [
                {"id": voice_id, "name": voice_id.replace('_', ' ').title()} 
                for voice_id in SUPPORTED_VOICES[kokoro_code]
            ]
            languages.append(
                LanguageVoice(
                    language_code=lang_code,
                    language_name=lang_name,
                    voices=voice_data
                )
            )
    
    return SupportedLanguagesResponse(languages=languages)


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the video generator API.
    """
    return {"status": "healthy", "version": "1.0.0"}


@router.post(
    "/cancel/{job_id}",
    response_model=JobResponse,
    responses={
        200: {"description": "Job cancellation request accepted."},
        404: {"description": "Job not found."},
        409: {"description": "Job cannot be cancelled (e.g., already completed/failed/cancelled)."},
        500: {"description": "Internal server error during cancellation."},
        503: {"description": "Job tracking service unavailable."}
    }
)
async def cancel_video_job(job_id: str = Path(..., description="The ID of the job to cancel")):
    """
    Request cancellation of a queued or processing video generation job.
    """
    try:
        cancelled_job_data = cancel_job(job_id)
        # Return the updated job data after cancellation attempt
        return JobResponse(
            job_id=cancelled_job_data["job_id"],
            status=JobStatus(cancelled_job_data["status"]),
            created_at=cancelled_job_data["created_at"],
            topic=cancelled_job_data["topic"],
            estimated_completion=cancelled_job_data.get("estimated_completion"),
            progress=cancelled_job_data.get("progress", 0.0)
        )
    except HTTPException as e:
        # Re-raise HTTP exceptions from cancel_job (like 404, 409, 503)
        raise e
    except Exception as e:
        # Catch any other unexpected errors during cancellation
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")
