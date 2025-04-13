import os
import argparse
import logging
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

from src.utils import ensure_dir_exists, cleanup_dir, logger
from src.content_generator import generate_educational_content
from src.audio_generator import generate_audio, get_default_voice_for_language, SUPPORTED_VOICES, LANGUAGE_CODE_MAP, DEFAULT_KOKORO_LANG_CODE

from src.diagram_renderer import render_visual_element
from src.animation_generator import generate_animation_scene
from src.video_composer import compose_final_video

# Load environment variables from .env file located in ../config relative to this script
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Configuration & Paths ---
# Base directory of the project (edu_video_generator)
PROJECT_BASE_DIR = Path(__file__).parent.parent.resolve()
ASSETS_DIR = PROJECT_BASE_DIR / os.getenv("ASSETS_DIR", "assets")
OUTPUT_DIR = PROJECT_BASE_DIR / os.getenv("OUTPUT_DIR", "output")

# Subdirectories within assets
AUDIO_ASSETS_DIR = ASSETS_DIR / "audio"
# DIAGRAM_ASSETS_DIR will store both diagrams and charts
DIAGRAM_ASSETS_DIR = ASSETS_DIR / "diagrams"
MANIM_ASSETS_DIR = ASSETS_DIR / "manim_videos"
TEMP_ASSETS_DIR = ASSETS_DIR / "temp"
CACHE_DIR = ASSETS_DIR / "cache" # For Gemini cache, etc.

# Max workers for parallel processing
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4")) # Adjust based on system resources

# Updated process_section function signature to accept specific voice
def process_section(section_index: int, section_data: Dict[str, Any], use_animation_cache: bool, language: str, voice: str) -> Dict[str, Optional[Any]]:
    """
    Processes a single section: generates audio (with specific language and voice),
    renders visual element (if any), generates Manim animation synchronized to audio (with optional caching).

    Args:
        section_index: Index of the section.
        section_data: Dictionary containing data for the section (narration, timed elements).
        use_animation_cache: Flag to control Manim animation caching.
        language: Language code for TTS (e.g., "en-US").
        voice: Specific voice name to use for TTS (e.g., "af_heart").

    Returns a dictionary containing paths/data for the generated assets.
    Keys: 'audio_path', 'visual_element_path', 'animation_path', 'audio_duration'. Values are None if generation failed.
    """
    logger.info(f"--- Starting processing for Section {section_index}: {section_data.get('title', 'Untitled')} ---")
    section_results = {
        "audio_path": None,
        "visual_element_path": None,
        "animation_path": None,
        "audio_duration": None,
    }
    narration_script = section_data.get("narration_script")
    timed_elements = section_data.get("timed_on_screen_elements")

    if not narration_script:
        logger.error(f"Section {section_index} has no narration_script. Skipping.")
        return section_results
    if not timed_elements or not isinstance(timed_elements, list):
         logger.error(f"Section {section_index}: Invalid or missing 'timed_on_screen_elements'. Skipping.")
         return section_results

    # 1. Generate Audio (passing specific language and voice)
    try:
        # Voice is now passed directly to this function
        logger.info(f"Section {section_index}: Generating audio using voice '{voice}' for language '{language}'.")

        # Pass language and the specific voice determined in main()
        audio_path, total_audio_duration, _ = generate_audio(
            section_index=section_index,
            narration_script=narration_script,
            output_dir=str(AUDIO_ASSETS_DIR),
            language=language,
            voice=voice # Pass the specific voice
        )
        if audio_path and total_audio_duration is not None:
            section_results["audio_path"] = audio_path
            section_results["audio_duration"] = total_audio_duration
            logger.info(f"Section {section_index}: Audio generated successfully (Lang: {language}, Duration: {total_audio_duration:.2f}s).")
        else:
            logger.error(f"Section {section_index}: Audio generation failed.")
            return section_results # Stop processing this section if audio fails
    except Exception as e:
        logger.error(f"Section {section_index}: Unexpected error during audio generation: {e}", exc_info=True)
        return section_results

    # 2. Render Visual Element (Diagram or Chart) - Find first one in timed_elements
    visual_element_path = None
    try:
        for element in timed_elements:
            element_type = element.get("type")
            element_content = element.get("content")
            if element_type in ["diagram", "chart_data"] and element_content:
                logger.info(f"Section {section_index}: Found visual element of type '{element_type}'. Attempting to render.")
                visual_element_path = render_visual_element(
                    section_index=section_index,
                    element_type=element_type,
                    element_content=element_content,
                    output_dir=str(DIAGRAM_ASSETS_DIR),
                    temp_dir=str(TEMP_ASSETS_DIR)
                )
                if visual_element_path:
                    section_results["visual_element_path"] = visual_element_path
                    logger.info(f"Section {section_index}: Visual element rendered successfully to {visual_element_path}.")
                else:
                    logger.warning(f"Section {section_index}: Visual element rendering failed or was skipped.")
                break # Only render the first visual element found per section
        if not visual_element_path:
             logger.info(f"Section {section_index}: No diagram or chart data found in timed elements.")

    except Exception as e:
        logger.error(f"Section {section_index}: Unexpected error during visual element rendering: {e}", exc_info=True)
        # Continue without visual element if rendering fails

    # 3. Generate Animation (Requires audio duration and timed_elements)
    try:
        # Pass the potentially None visual_element_path
        animation_path = generate_animation_scene(
            section_index=section_index,
            timed_elements=timed_elements,
            diagram_path=section_results.get("visual_element_path"), # Use the rendered path
            audio_duration=section_results["audio_duration"], # Pass TOTAL audio duration
            output_dir=str(MANIM_ASSETS_DIR),
            temp_dir=str(TEMP_ASSETS_DIR),
            use_cache=use_animation_cache
        )
        if animation_path:
            section_results["animation_path"] = animation_path
            logger.info(f"Section {section_index}: Animation generated successfully.")
        else:
            logger.error(f"Section {section_index}: Animation generation failed.")
            # If animation fails, the final composition will skip this section.
    except Exception as e:
        import traceback
        logger.error(f"Section {section_index}: Unexpected error during animation generation:")
        logger.error(f"  Error Type: {type(e).__name__}")
        logger.error(f"  Error Details: {e}")
        logger.error(f"  Traceback:\n{traceback.format_exc()}")

    logger.info(f"--- Finished processing for Section {section_index} ---")
    return section_results


def main():
    parser = argparse.ArgumentParser(description="Generate an educational video from a topic.")
    parser.add_argument("topic", help="The topic for the educational video.")
    parser.add_argument("-o", "--output", help="Output video filename (e.g., 'my_video.mp4'). Default: <topic_slug>_<language>.mp4", default=None)
    # Add language argument
    parser.add_argument("--language", default="en-US", help="TTS language code (e.g., en-US, en-GB, hi-IN, es-ES)")
    # Add optional voice argument
    parser.add_argument("--voice", default=None, help="Specific TTS voice name (e.g., af_bella, hf_beta). Overrides language default.")
    parser.add_argument("--cleanup", action="store_true", help="Clean up intermediate asset files after generation.")
    parser.add_argument("--skip-content-cache", action="store_true", help="Force regeneration of content from Gemini, ignoring cache.")
    parser.add_argument("--no-animation-cache", action="store_true", help="Disable caching of rendered Manim animations.")

    args = parser.parse_args()
    topic = args.topic
    language = args.language # Get language from args
    voice_override = args.voice # Get optional voice override
    skip_content_cache = args.skip_content_cache
    use_animation_cache = not args.no_animation_cache

    # Determine output filename
    if args.output:
        output_filename = args.output
        if not output_filename.lower().endswith(".mp4"):
            output_filename += ".mp4"
    else:
        topic_slug = "".join(c if c.isalnum() else "_" for c in topic).lower().strip('_')
        # Include language in default filename for clarity
        output_filename = f"{topic_slug}_{language}.mp4"

    final_output_path = OUTPUT_DIR / output_filename

    # --- Setup ---
    start_time = time.time()
    logger.info(f"Starting video generation for topic: '{topic}' in language: '{language}'")
    logger.info(f"Final output will be saved to: {final_output_path}")

    ensure_dir_exists(str(ASSETS_DIR))
    ensure_dir_exists(str(OUTPUT_DIR))
    ensure_dir_exists(str(AUDIO_ASSETS_DIR))
    ensure_dir_exists(str(DIAGRAM_ASSETS_DIR))
    ensure_dir_exists(str(MANIM_ASSETS_DIR))
    ensure_dir_exists(str(TEMP_ASSETS_DIR))
    ensure_dir_exists(str(CACHE_DIR))

    # --- Step 1: Generate Content (passing language) ---
    logger.info(f"Step 1: Generating script content from Gemini API for language '{language}'...")
    try:
        if skip_content_cache:
             logger.warning("Skipping content cache (--skip-content-cache) is not fully implemented yet.")
             pass

        # Pass language to content generator
        script_data = generate_educational_content(topic, language=language)
        logger.info("Script content generated successfully.")

        script_save_path = OUTPUT_DIR / f"{topic_slug}_{language}_script.json"
        try:
            with open(script_save_path, "w", encoding='utf-8') as f: # Ensure utf-8 encoding
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved generated script for debugging to: {script_save_path}")
        except Exception as save_e:
            logger.error(f"Failed to save script data to {script_save_path}: {save_e}")

    except (ValueError, RuntimeError) as e:
        logger.error(f"Failed to generate script content: {e}")
        return
    except Exception as e:
        import traceback
        logger.error(f"An unexpected error occurred during content generation: {e}", exc_info=True)
        return

    sections = script_data.get("sections", [])
    if not sections:
        logger.error("No sections found in the generated script content. Aborting.")
        return

    # --- Step 2: Process Sections in Parallel (passing language and chosen voice) ---
    logger.info(f"Step 2: Processing {len(sections)} sections in parallel (max_workers={MAX_WORKERS})...")
    processed_assets = [None] * len(sections)
    futures = {}

    # Determine the voice to use (either override or default)
    final_voice = voice_override
    if not final_voice:
        final_voice = get_default_voice_for_language(language)
        logger.info(f"No voice specified, using default for language '{language}': '{final_voice}'")
    else:
        # Validate the specified voice override
        kokoro_code = LANGUAGE_CODE_MAP.get(language, DEFAULT_KOKORO_LANG_CODE)
        if kokoro_code not in SUPPORTED_VOICES or final_voice not in SUPPORTED_VOICES[kokoro_code]:
            logger.warning(f"Specified voice '{final_voice}' is not valid for language '{language}' (Kokoro code '{kokoro_code}'). Falling back to default.")
            final_voice = get_default_voice_for_language(language)
            logger.warning(f"Using default voice: '{final_voice}'")
        else:
             logger.info(f"Using specified voice: '{final_voice}' for language '{language}'")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for i, section in enumerate(sections):
            # Pass language AND the determined final_voice to process_section
            future = executor.submit(process_section, i, section, use_animation_cache, language, final_voice)
            futures[future] = i

        for future in as_completed(futures):
            original_index = futures[future]
            try:
                result = future.result()
                processed_assets[original_index] = result
                logger.info(f"Completed processing for section {original_index}.")
            except Exception as e:
                logger.error(f"An error occurred processing section {original_index}: {e}", exc_info=True)

    logger.info("Finished parallel processing of sections.")

    # Filter out sections that failed critical steps (missing animation or audio)
    valid_section_assets = [assets for assets in processed_assets if assets and assets.get('animation_path') and assets.get('audio_path')]

    if not valid_section_assets:
         logger.error("No sections were successfully processed with both audio and animation. Cannot compose video.")
         return

    if len(valid_section_assets) < len(sections):
         logger.warning(f"Only {len(valid_section_assets)} out of {len(sections)} sections were processed successfully.")

    # --- Step 3: Compose Final Video ---
    logger.info("Step 3: Composing final video...")
    composition_success = compose_final_video(valid_section_assets, str(final_output_path))

    if not composition_success:
        logger.error("Failed to compose the final video.")
        return

    # --- Step 4: Cleanup (Optional) ---
    if args.cleanup:
        logger.info("Step 4: Cleaning up intermediate asset files...")
        cleanup_dir(str(AUDIO_ASSETS_DIR))
        cleanup_dir(str(DIAGRAM_ASSETS_DIR))
        cleanup_dir(str(MANIM_ASSETS_DIR))
        cleanup_dir(str(TEMP_ASSETS_DIR))
        logger.info("Cleanup complete.")
    else:
        logger.info("Skipping cleanup of intermediate files.")

    # --- Finish ---
    end_time = time.time()
    total_time = end_time - start_time
    logger.info("=" * 30)
    logger.info(f"Video generation process completed successfully!")
    logger.info(f"Output file: {final_output_path}")
    logger.info(f"Total time taken: {total_time:.2f} seconds")
    logger.info("=" * 30)


if __name__ == "__main__":
    main()
