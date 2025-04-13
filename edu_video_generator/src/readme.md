# Educational Video Generator API

This API provides endpoints to generate educational videos based on a given topic. It handles content generation, text-to-speech, animation rendering, and video composition asynchronously.

## Features

*   **Asynchronous Video Generation:** Submit a topic and receive a job ID to track progress.
*   **Job Status Tracking:** Check the status of ongoing or completed video generation jobs.
*   **Video Download:** Download the final MP4 video once generation is complete.
*   **Language & Voice Support:** Specify language and voice for the video's narration.
*   **Caching:** Caches generated content and animations to speed up subsequent requests for the same topic.
*   **Health Check:** Endpoint to verify API service status.

## Prerequisites

*   **Python:** Version 3.8+
*   **Redis:** A running Redis server instance (used by Celery for task queuing and results).
*   **Manim Dependencies:** Manim requires several system-level dependencies:
    *   FFmpeg
    *   LaTeX distribution (e.g., TeX Live, MiKTeX)
    *   Cairo
    *   Pango
    (Refer to the official [Manim Installation Guide](https://docs.manim.community/en/stable/installation/index.html) for OS-specific instructions.)
*   **Mermaid CLI (`mmdc`):** Required if generating diagrams using Mermaid syntax within the content. Install via npm: `npm install -g @mermaid-js/mermaid-cli`

## Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>/edu_video_generator
    ```

2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
   
    For Ubuntu:
    ```bash
    sudo apt install pkg-config libpango1.0-dev libcairo2-dev libx11-dev
    ```

    For Arch:
    ```bash
    sudo pacman -S libx11 cairo
    ```

    ```bash
    pip install -r requirements.txt
    ```
    *Note: Installing `torch` might take time. Ensure you have a stable internet connection.*

4.  **Configure Environment Variables:**
    *   Copy the sample environment file:
        ```bash
        cp config/sample.env config/.env
        ```
    *   Edit `config/.env` and fill in the required values:
        *   `GEMINI_API_KEY`: Your API key from Google AI Studio or Google Cloud.
        *   `AUDIO_GENERATOR_API_URL`: The URL of your running audio generation service (e.g., the one from `audio_api_service`).
        *   Update other variables like `OUTPUT_DIR`, `ASSETS_DIR` if needed. See the [Configuration](#configuration) section for details.

## Running the Service

1.  **Start Redis Server:** Ensure your Redis server is running. (Consult Redis documentation if needed).

2.  **Start Celery Worker:** Open a terminal, navigate to the project root (one level above `edu_video_generator`), activate the virtual environment, and run:
    ```bash
    celery -A edu_video_generator.src.api.service worker --loglevel=info -P solo
    ```
    *(Note: Using `-P solo` might be necessary on Windows or for simpler setups.)*

3.  **Start API Server:** Open another terminal, navigate to the project root, activate the virtual environment, and run:
    ```bash
    cd edu_video_generator
    uvicorn src.api_server:app --host 0.0.0.0 --port <API_PORT> [--reload]
    ```
    *   Replace `<API_PORT>` with the port number (default is 4567).
    *   Add `--reload` for development to automatically restart the server on code changes.

The API documentation will be available at `http://localhost:<API_PORT>/docs` (Swagger UI) and `http://localhost:<API_PORT>/redoc` (ReDoc).

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### 1. Generate Video

*   **Endpoint:** `POST /generate_video/`
*   **Description:** Submits a request to generate an educational video or retrieves a cached result. If the exact request (topic, language, voice) has been successfully completed recently, details of the cached job are returned with a **200 OK** status. Otherwise, a new job is queued, and its details are returned with a **202 Accepted** status. Video generation happens asynchronously for new jobs.
*   **Request Body:** (`application/json`)
    ```json
    {
      "topic": "String - The topic for the educational video (Required)",
      "language": "String - TTS language code (e.g., en-US, hi-IN) (Default: 'en-US')",
      "voice": "String - Specific TTS voice name (Optional)",
      "cleanup": "Boolean - Clean up intermediate files after completion (Default: false)",
      "skip_content_cache": "Boolean - Force regeneration of content (Default: false)",
      "no_animation_cache": "Boolean - Disable caching of animations (Default: false)"
    }
    ```
    *Example:*
    ```json
    {
      "topic": "Photosynthesis",
      "language": "en-US",
      "voice": "en-US-BrianNeural"
    }
    ```
*   **Success Responses:**
    *   `202 Accepted`: New job successfully queued.
        ```json
        {
          "job_id": "f58d7a6c-e1c2-4a7b-b1e4-d6a2bf2e7e9a",
          "status": "queued",
          "created_at": "2025-04-13T10:00:00",
          "topic": "Photosynthesis",
          "estimated_completion": null,
          "progress": 0.0
        }
        ```
    *   `200 OK`: Request matched a completed job in cache.
        ```json
        {
          "job_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
          "status": "completed",
          "created_at": "2025-04-12T15:30:00",
          "topic": "Photosynthesis",
          "estimated_completion": "2025-04-12T15:45:00",
          "progress": 100.0
        }
        ```
*   **Error Responses:**
    *   `422 Unprocessable Entity`: Invalid request body.
    *   `429 Too Many Requests`: Resource limits exceeded (if implemented).
    *   `500 Internal Server Error`: Failed to create job.
    *   `503 Service Unavailable`: Job tracking service unavailable (if implemented).

### 2. Get Job Status

*   **Endpoint:** `GET /jobs/{job_id}`
*   **Description:** Checks the status of a video generation job.
*   **Path Parameter:**
    *   `job_id` (string, required): The unique ID of the job.
*   **Success Response:** (`200 OK`)
    ```json
    {
      "job_id": "f58d7a6c-e1c2-4a7b-b1e4-d6a2bf2e7e9a",
      "status": "processing", // Can be queued, processing, completed, failed
      "created_at": "2025-04-13T10:00:00",
      "topic": "Photosynthesis",
      "estimated_completion": "2025-04-13T10:15:00",
      "progress": 45.5
    }
    ```
*   **Error Responses:**
    *   `404 Not Found`: Job with the specified ID not found.
    *   `422 Unprocessable Entity`: Invalid `job_id` format.

### 3. Get Video

*   **Endpoint:** `GET /video/{job_id}`
*   **Description:** Downloads the generated MP4 video for a completed job.
*   **Path Parameter:**
    *   `job_id` (string, required): The unique ID of the completed job.
*   **Success Response:** (`200 OK`)
    *   Returns the video file (`video/mp4`). The filename will be suggested as `<topic_slug>_<job_id>.mp4`.
*   **Error Responses:**
    *   `400 Bad Request`: Video is not ready (job status is not 'completed').
    *   `404 Not Found`: Job with the specified ID not found, or the video file is missing.
    *   `422 Unprocessable Entity`: Invalid `job_id` format.

### 4. Get Supported Languages

*   **Endpoint:** `GET /languages`
*   **Description:** Retrieves a list of supported languages and their available voices for TTS.
*   **Success Response:** (`200 OK`)
    ```json
    {
      "languages": [
        {
          "language_code": "en-US",
          "language_name": "American English",
          "voices": [
            {"id": "en_us_cmu_arctic_slt", "name": "En Us Cmu Arctic Slt"}, 
            {"id": "en_us_hifi_tts_female", "name": "En Us Hifi Tts Female"} 
            // ... other voices for en-US
          ]
        },
        {
          "language_code": "hi-IN",
          "language_name": "Hindi",
          "voices": [
             {"id": "kokoro_hi_in_female_001", "name": "Kokoro Hi In Female 001"}
             // ... other voices for hi-IN
          ]
        }
        // ... other languages
      ]
    }
    ```
*   **Error Responses:** None specific beyond standard server errors.

### 5. Health Check

*   **Endpoint:** `GET /health`
*   **Description:** Simple health check endpoint.
*   **Success Response:** (`200 OK`)
    ```json
    {
      "status": "healthy",
      "version": "1.0.0" 
    }
    ```
*   **Error Responses:** None specific beyond standard server errors.

## Configuration

Environment variables are loaded from `config/.env`.

*   `GEMINI_API_KEY`: **Required.** Your API key for Google Gemini, used for content generation.
*   `AUDIO_GENERATOR_API_URL`: **Required.** The base URL for the external Text-to-Speech API service.
*   `OUTPUT_DIR`: Directory (relative to `edu_video_generator`) to store final video outputs. Default: `output/`.
*   `ASSETS_DIR`: Directory (relative to `edu_video_generator`) for intermediate assets (audio, diagrams, etc.). Default: `assets/`.
*   `MAX_WORKERS`: Maximum number of concurrent threads/processes for tasks like animation rendering within the Celery worker. Default: `4`.
*   `MERMAID_CLI_PATH`: Optional. Full path to the `mmdc` executable if not in the system's PATH.
