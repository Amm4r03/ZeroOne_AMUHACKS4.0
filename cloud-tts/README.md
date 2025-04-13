# CloudTTS FastAPI Proxy

This project provides a simple FastAPI web service that acts as a proxy to the `cloudtts.com` text-to-speech API. It allows you to synthesize speech by sending text and configuration options to a local endpoint.

## Features

*   Synthesizes text using various voices available on `cloudtts.com`.
*   Configurable speech rate (0.1 to 2.0) and volume (0.0 to 1.0).
*   Validates input parameters, including voice selection based on available voices.
*   Returns the synthesized audio directly as an MP3 file.

## Setup

1.  **Clone/Download:** Get the project files (`main.py`, `requirements.txt`, `voicedata.txt`).
2.  **Install Dependencies:** Make sure you have Python 3 installed. Then, install the required packages using pip:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

1.  **Start the server:** Run the main Python script:
    ```bash
    python3 main.py
    ```
2.  The server will start, typically on `http://127.0.0.1:8000`.

## Using the API

You can interact with the API using tools like `curl`, API clients (Postman, Insomnia), or by integrating it into other applications.

**Endpoint:** `POST /tts`

**Request Body (JSON):**

```json
{
  "text": "Your text to synthesize",
  "voice": "en-US-AriaNeural", // Choose a valid VoiceURI from voicedata.txt
  "rate": 1.0,                 // Optional, default: 1.0 (Range: 0.1 - 2.0)
  "volume": 1.0                // Optional, default: 1.0 (Range: 0.0 - 1.0)
}
```

**Example using `curl`:**

This command sends "Hello world" to the API using the `en-US-AriaNeural` voice and saves the output as `output.mp3`.

```bash
curl -X POST http://127.0.0.1:8000/tts \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello world", "voice": "en-US-AriaNeural"}' \
     --output output.mp3
```

**Response:**

*   **Success (200 OK):** The raw MP3 audio data.
*   **Error (4xx/5xx):** A JSON object describing the error (e.g., validation error, rate limit, upstream API error).

## API Documentation

Interactive API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs` when the server is running. You can use this interface to explore the endpoint and make test requests directly from your browser. Note that the audio preview within Swagger UI might not work correctly for binary audio data.
