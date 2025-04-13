# Project: AI-Powered Video Generation Suite

This project contains a collection of services and tools designed for generating educational videos and providing text-to-speech (TTS) capabilities.

## Project Structure

The repository is organized into the following main components:

*   **`edu_video_generator/`**: The core component responsible for generating educational videos. It takes a topic, uses AI (Gemini) to generate content, synthesizes audio using a TTS service, creates animations with Manim, and finally composes the video. It offers both a command-line interface and an asynchronous API for video generation tasks.
    *   [Detailed README for Edu Video Generator](./edu_video_generator/README.md)
    *   [Detailed README for Edu Video Generator API](./edu_video_generator/src/readme.md)
*   **`audio_api_service/`**: A FastAPI service providing Text-to-Speech functionality using the `kokoro` library locally. It exposes an API endpoint to convert text into WAV audio format.
    *   [Detailed README for Audio API Service](./audio_api_service/README.md)
*   **`cloud-tts/`**: A FastAPI service acting as a proxy to the external `cloudtts.com` API. It allows synthesizing speech using cloud-based voices via a local endpoint.
    *   [Detailed README for Cloud TTS Proxy](./cloud-tts/README.md)
*   **`tests/`**: Contains unit and integration tests for various parts of the project, ensuring functionality and correctness.

## Overview

The primary goal of this project is facilitated by the `edu_video_generator`. This module integrates the other components (or external services like Gemini) to automate the creation of educational video content. Users can provide a topic, and the system handles script generation, voiceover creation (using one of the TTS services), and visual animation rendering.

The TTS capabilities are provided by two distinct services:
1.  `audio_api_service`: For local, potentially offline TTS generation using the Kokoro engine.
2.  `cloud-tts`: For leveraging the wider range of voices available through the `cloudtts.com` platform.

The `edu_video_generator` can be configured to use one of these TTS services based on requirements (e.g., voice preference, offline capability).

Please refer to the individual README files linked above for detailed setup, configuration, and usage instructions for each component.
