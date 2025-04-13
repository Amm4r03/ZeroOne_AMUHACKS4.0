import os
import logging
import re
from typing import Tuple, Optional, List, Any
from dotenv import load_dotenv
import requests
import soundfile as sf
from pydub import AudioSegment

from src.utils import ensure_dir_exists, logger

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- API Configuration ---
AUDIO_GENERATOR_API_URL = os.getenv("AUDIO_GENERATOR_API_URL")
if not AUDIO_GENERATOR_API_URL:
    logger.error("AUDIO_GENERATOR_API_URL environment variable is not set. Cannot generate audio via API.")


# --- Language & Voice Mappings (Mirrored from api.py for client-side logic) ---
LANGUAGE_CODE_MAP = {
    'en-US': 'a', # American English
    'en-GB': 'b', # British English
    'es-ES': 'e', # Spanish
    'fr-FR': 'f', # French
    'hi-IN': 'h', # Hindi
    'it-IT': 'i', # Italian
    'ja-JP': 'j', # Japanese
    'pt-BR': 'p', # Brazilian Portuguese
    'zh-CN': 'z', # Mandarin Chinese
}
DEFAULT_KOKORO_LANG_CODE = 'a' # Default if language not provided or not mapped

SUPPORTED_VOICES = {
    'a': [ # American English
        'af_heart', 'af_alloy', 'af_aoede', 'af_bella', 'af_jessica',
        'af_kore', 'af_nicole', 'af_nova', 'af_river', 'af_sarah',
        'af_sky', 'am_adam', 'am_echo', 'am_eric', 'am_fenrir',
        'am_liam', 'am_michael', 'am_onyx', 'am_puck', 'am_santa'
    ],
    'b': [ # British English
        'bf_alice', 'bf_emma', 'bf_isabella', 'bf_lily', 'bm_daniel',
        'bm_fable', 'bm_george', 'bm_lewis'
    ],
    'j': [ # Japanese
        'jf_alpha', 'jf_gongitsune', 'jf_nezumi', 'jf_tebukuro', 'jm_kumo'
    ],
    'z': [ # Mandarin Chinese
        'zf_xiaobei', 'zf_xiaoni', 'zf_xiaoxiao', 'zf_xiaoyi',
        'zm_yunjian', 'zm_yunxi', 'zm_yunxia', 'zm_yunyang'
    ],
    'e': [ # Spanish
        'ef_dora', 'em_alex', 'em_santa'
    ],
    'f': [ # French
        'ff_siwis'
    ],
    'h': [ # Hindi
        'hf_alpha', 'hf_beta', 'hm_omega', 'hm_psi'
    ],
    'i': [ # Italian
        'if_sara', 'im_nicola'
    ],
    'p': [ # Brazilian Portuguese
        'pf_dora', 'pm_alex', 'pm_santa'
    ]
}
# Define default voices per language (using the first one as requested)
DEFAULT_VOICES = {lang: voices[0] for lang, voices in SUPPORTED_VOICES.items()}
# Optionally override specific defaults if the first isn't ideal (e.g., af_heart for 'a')
DEFAULT_VOICES['a'] = 'af_heart'


# --- Helper Functions ---
def get_wav_duration(file_path: str) -> Optional[float]:
    """Calculates the duration of a WAV file using soundfile."""
    try:
        with sf.SoundFile(file_path) as f:
            frames = f.frames
            rate = f.samplerate
            duration = frames / float(rate) if rate > 0 else 0
            return duration
    except Exception as e:
        logger.error(f"Failed to get duration for WAV file {file_path} using soundfile: {e}")
        # Fallback attempt with pydub
        try:
            audio = AudioSegment.from_wav(file_path)
            duration = len(audio) / 1000.0
            logger.warning(f"Used pydub fallback for duration of {os.path.basename(file_path)}: {duration:.3f}s")
            return duration
        except Exception as pd_e:
            logger.error(f"Pydub fallback failed for {file_path}: {pd_e}")
            return None

# Regex to find pause markers and capture the duration
PAUSE_MARKER_REGEX = re.compile(r"\[PAUSE=(\d+(?:\.\d+)?)\]")

def get_default_voice_for_language(language: str) -> str:
    """Gets the default Kokoro voice name for a given user language code (e.g., 'en-US')."""
    kokoro_code = LANGUAGE_CODE_MAP.get(language, DEFAULT_KOKORO_LANG_CODE)
    return DEFAULT_VOICES.get(kokoro_code, DEFAULT_VOICES[DEFAULT_KOKORO_LANG_CODE]) # Fallback to overall default

def parse_script_with_pauses(script: str) -> List[Tuple[str, Any]]:
    """Parses script into ('speech', text) or ('pause', duration_float) segments."""
    segments = []
    last_end = 0
    for match in PAUSE_MARKER_REGEX.finditer(script):
        start, end = match.span()
        pause_duration = float(match.group(1))

        # Add preceding text segment if it exists
        text_segment = script[last_end:start].strip()
        if text_segment:
            segments.append(('speech', text_segment))

        # Add pause segment
        segments.append(('pause', pause_duration))
        last_end = end

    # Add any remaining text after the last pause
    remaining_text = script[last_end:].strip()
    if remaining_text:
        segments.append(('speech', remaining_text))

    return segments

def call_tts_api(text_segment: str, segment_index: int, section_index: int, language: str, voice: str) -> Optional[AudioSegment]: # Added voice parameter
    """
    Calls the TTS API for a single text segment and returns an AudioSegment.
    Includes language and voice parameters for TTS selection.
    """
    if not AUDIO_GENERATOR_API_URL:
        logger.error("Audio Generator API URL is not configured.")
        return None

    # Include language and voice in the payload
    payload = {"text": text_segment, "language": language, "voice": voice}
    headers = {"Accept": "audio/wav"}
    temp_filename = f"temp_section_{section_index}_segment_{segment_index}.wav"

    try:
        logger.debug(f"Requesting TTS for section {section_index}, segment {segment_index}: '{text_segment[:50]}...'")
        response = requests.post(AUDIO_GENERATOR_API_URL, json=payload, headers=headers, stream=True, timeout=300) # Shorter timeout for segments

        if response.status_code == 200:
            # Save temporarily to load with pydub
            with open(temp_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            # Load into AudioSegment
            audio_segment = AudioSegment.from_wav(temp_filename)
            os.remove(temp_filename) # Clean up temporary file
            logger.debug(f"Successfully generated audio for segment {segment_index}")
            return audio_segment
        else:
            error_detail = response.text
            logger.error(f"API request failed for segment {segment_index}. Status: {response.status_code}, Detail: {error_detail}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to API for segment {segment_index}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing segment {segment_index}: {e}", exc_info=True)
        if os.path.exists(temp_filename):
            os.remove(temp_filename) # Ensure cleanup on error
        return None

# Main function updated to handle pauses manually and accept language and voice
def generate_audio(section_index: int, narration_script: str, output_dir: str, language: str, voice: str) -> Tuple[Optional[str], Optional[float], Optional[List[float]]]: # Added voice parameter
    """
    Generates audio by calling the TTS API for speech segments and inserting silence
    manually for [PAUSE=X.X] markers, using the specified language and voice.

    Args:
        section_index: Index of the video section.
        narration_script: The script text including pause markers.
        output_dir: Directory to save the final audio file.
        language: The language code (e.g., "en-US") to pass to the TTS API.
        voice: The voice name (e.g., "af_heart") to pass to the TTS API.

    Returns:
        Tuple containing:
        - Path to the generated audio file (str) or None on failure.
        - Total duration of the audio in seconds (float) or None on failure.
        - List of speech segment durations (currently always None).
    """
    if not AUDIO_GENERATOR_API_URL:
        logger.error("Audio Generator API URL is not configured. Cannot proceed.")
        return None, None, None

    ensure_dir_exists(output_dir)
    final_output_filename = f"section_{section_index}_audio.wav"
    final_output_filepath = os.path.join(output_dir, final_output_filename)
    logger.info(f"Generating audio with manual pauses for section {section_index}...")

    # 1. Parse the script
    parsed_segments = parse_script_with_pauses(narration_script)
    if not parsed_segments:
        logger.warning(f"Narration script for section {section_index} is empty or contains only pauses.")
        # Create a short silent file? Or return error? Let's return error for now.
        return None, 0.0, None # Indicate failure but 0 duration

    # 2. Generate audio/silence for each segment
    final_audio = AudioSegment.empty()
    segment_counter = 0
    for segment_type, segment_data in parsed_segments:
        if segment_type == 'speech':
            # Pass the language and voice parameters to the API call
            audio_clip = call_tts_api(segment_data, segment_counter, section_index, language, voice)
            if audio_clip is None:
                logger.error(f"Failed to generate audio for a speech segment in section {section_index}. Aborting audio generation for this section.")
                return None, None, None # Indicate failure
            final_audio += audio_clip
            segment_counter += 1
        elif segment_type == 'pause':
            pause_duration_ms = int(segment_data * 1000) # pydub uses milliseconds
            logger.debug(f"Adding {pause_duration_ms}ms pause.")
            # Use AudioSegment.silent() instead of SilenceGenerator
            silence_clip = AudioSegment.silent(duration=pause_duration_ms)
            # Ensure silence clip has same channels as previous audio clip if possible
            # Note: AudioSegment.silent() defaults to mono, 16 bit, 44100 Hz.
            # We might need to adjust frame rate/channels if the TTS API returns something different,
            # but pydub usually handles concatenation well. Let's keep it simple for now.
            # if len(final_audio) > 0:
            #     silence_clip = silence_clip.set_frame_rate(final_audio.frame_rate).set_channels(final_audio.channels)
            final_audio += silence_clip
        else:
             logger.warning(f"Unknown segment type encountered: {segment_type}")


    # 3. Export the combined audio
    try:
        logger.info(f"Exporting combined audio to {final_output_filepath}")
        # Use WAV format consistent with previous implementation
        final_audio.export(final_output_filepath, format="wav")
    except Exception as e:
        logger.error(f"Failed to export combined audio for section {section_index}: {e}", exc_info=True)
        return None, None, None

    # 4. Calculate final duration
    total_duration = len(final_audio) / 1000.0 # Duration in seconds
    logger.info(f"Successfully generated combined audio for section {section_index} (Duration: {total_duration:.2f}s).")

    # Segment durations are complex to calculate accurately with this method, return None
    return final_output_filepath, total_duration, None


# Example usage would now test this combined flow.
# if __name__ == '__main__':
#     print("Testing Audio Generation with Manual Pauses...")
#     test_script = "Hello there.[PAUSE=1.0] This is a test script [PAUSE=0.5] with pauses."
#     test_output_dir = "../assets/audio_test" # Adjust path as needed
#     filepath, duration, _ = generate_audio(999, test_script, test_output_dir)
#     if filepath:
#         print(f"Generated test audio: {filepath}, Duration: {duration:.2f}s")
#     else:
#         print("Failed to generate test audio.")
