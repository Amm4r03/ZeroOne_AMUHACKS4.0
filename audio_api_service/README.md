# Kokoro TTS Audio API Service

A simple FastAPI service that provides Text-to-Speech (TTS) audio generation using the `kokoro` library.

## Features

*   Generates WAV audio files from text input.
*   Supports multiple languages and voices provided by Kokoro.
*   Allows inserting pauses in the narration using `[PAUSE=seconds]` syntax.
*   Provides a health check endpoint.
*   Uses background tasks for cleaning up temporary audio files.

## Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)
*   **(Optional but Recommended)** `git` for cloning the repository.

## Installation

1.  **Clone the repository (Optional):**
    ```bash
    git clone repourl
    # If you have the code already, navigate to the audio_api_service directory
    cd path/to/audio_api_service
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**

    Setuptools (>61) needed:
    ```bash
    pip install --upgrade pip setuptools wheel
    ```

    For Arch Linux:
    ```bash
    yay -S mecab-git
    pacman -S cmake
    ```
    
    For Ubuntu:
    ```bash
    sudo apt install mecab libmecab-dev mecab-ipadic-utf8 cmake
    ```

    ```bash
    pip3 install -r requirements.txt
    ```

    ```bash
    python3 -m unidic download
    ```

## Configuration

The service uses language codes and voice names defined within `api.py`.

*   **Languages:** The mapping from standard language codes (e.g., `en-US`) to Kokoro's internal codes (e.g., `a`) is defined in `LANGUAGE_CODE_MAP`.
*   **Voices:** Supported voices for each Kokoro language code are listed in `SUPPORTED_VOICES`. Default voices are defined in `DEFAULT_VOICES`.

You can modify these dictionaries in `api.py` if needed, but be aware that Kokoro must support the added languages/voices.

## Running the Service

Use `uvicorn` to run the FastAPI application defined in `main.py`:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

*   `--host 0.0.0.0`: Makes the server accessible on your network.
*   `--port 8000`: Specifies the port to run on.
*   `--reload`: Enables auto-reloading during development (remove for production).

The API will be available at `http://localhost:8000` (or your machine's IP address if accessing remotely). Interactive documentation (Swagger UI) is available at `http://localhost:8000/docs`.

## API Endpoints

### 1. Generate Audio

*   **Endpoint:** `POST /api/generate_audio/`
*   **Description:** Generates a WAV audio file from the provided text.
*   **Request Body (JSON):**
    ```json
    {
      "text": "Hello world. [PAUSE=1.5] This is a test narration.",
      "language": "en-US", // Optional: Defaults to 'en-US'
      "voice": "af_heart"   // Optional: Defaults to language-specific default
    }
    ```
    *   `text` (str, required): The text to convert to speech. Use `[PAUSE=seconds]` (e.g., `[PAUSE=0.5]`) to insert silence.
    *   `language` (str, optional): The language code (e.g., "en-US", "en-GB", "hi-IN", "ja-JP"). See `LANGUAGE_CODE_MAP` in `api.py` for supported codes. Defaults to "en-US".
    *   `voice` (str, optional): The specific voice name for the selected language. See `SUPPORTED_VOICES` in `api.py`. Defaults to the language's default voice if omitted or invalid.
*   **Success Response (200 OK):**
    *   **Content-Type:** `audio/wav`
    *   **Body:** The raw WAV audio data.
*   **Error Responses:**
    *   `422 Unprocessable Entity`: Invalid request body (e.g., missing `text`).
    *   `500 Internal Server Error`: Failed to initialize Kokoro or generate audio.

*   **Example (`curl`):**
    ```bash
    curl -X POST "http://localhost:8000/api/generate_audio/" \
         -H "Content-Type: application/json" \
         -d '{
               "text": "こんにちは、世界！ [PAUSE=1] これはテストです。",
               "language": "ja-JP",
               "voice": "jf_nezumi"
             }' \
         --output japanese_audio.wav
    ```

### 2. Health Check

*   **Endpoint:** `GET /api/health`
*   **Description:** Checks if the service is running and if the Kokoro library (`KPipeline`) was successfully imported.
*   **Success Response (200 OK):**
    ```json
    {
      "status": "ok",
      "message": "Kokoro library (KPipeline) is available. Initialization happens per request."
    }
    ```
*   **Error Response (if Kokoro import failed):**
    ```json
    {
      "status": "error",
      "message": "Kokoro library (KPipeline) is not available/importable."
    }
    ```
*   **Example (`curl`):**
    ```bash
    curl http://localhost:8000/api/health
    ```

## Notes

*   The service creates temporary directories for processing audio segments. These are automatically cleaned up after the audio file is sent using FastAPI's `BackgroundTasks`.
*   Logging provides information about the generation process, including language/voice selection and potential errors.
