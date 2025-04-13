import os
import sys
import logging

from edu_video_generator.src.animation_generator import generate_animation_scene
from edu_video_generator.src.utils import ensure_dir_exists, logger

# --- Test Configuration ---
TEST_SECTION_INDEX = 888 # Unique index for test
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "test_layout")
TEST_TEMP_DIR = os.path.join(os.path.dirname(__file__), "assets", "temp", "test_layout")
DUMMY_VISUAL_PATH = os.path.join(os.path.dirname(__file__), "assets", "temp", "dummy_visual.png")
TEST_AUDIO_DURATION = 15.0 # Arbitrary duration for timing test

# Define sample timed elements for testing layout
TEST_TIMED_ELEMENTS = [
    {"type": "text", "content": "Main Title for Layout Test", "start_time": 0, "end_time": 2},
    {"type": "text", "content": "This is the first line of content text.", "start_time": 2, "end_time": 5},
    {"type": "latex", "content": r"L = \frac{1}{2} m (\dot{x}^2 + \dot{y}^2) - V(x,y)", "start_time": 5, "end_time": 8},
    {"type": "text", "content": "Another line of text to check alignment.", "start_time": 8, "end_time": 11},
    # This element signals where the diagram should appear based on its timing,
    # but the actual path is passed directly to generate_animation_scene.
    {"type": "diagram", "content": "Reference to dummy_visual.png", "start_time": 11, "end_time": 14}
]

if __name__ == "__main__":
    logger.info("--- Starting Manim Layout Test ---")
    ensure_dir_exists(TEST_OUTPUT_DIR)
    ensure_dir_exists(TEST_TEMP_DIR)

    # Check if dummy visual exists
    if not os.path.exists(DUMMY_VISUAL_PATH):
        logger.error(f"Dummy visual not found at {DUMMY_VISUAL_PATH}. Please run create_dummy_image.py first.")
        sys.exit(1)

    logger.info(f"Using dummy visual: {DUMMY_VISUAL_PATH}")
    logger.info(f"Test output directory: {TEST_OUTPUT_DIR}")
    logger.info(f"Test temp directory: {TEST_TEMP_DIR}")

    # Call the animation generation function
    animation_path = generate_animation_scene(
        section_index=TEST_SECTION_INDEX,
        timed_elements=TEST_TIMED_ELEMENTS,
        diagram_path=DUMMY_VISUAL_PATH, # Pass the path to the dummy image
        audio_duration=TEST_AUDIO_DURATION,
        output_dir=TEST_OUTPUT_DIR, # Save test output separately
        temp_dir=TEST_TEMP_DIR,
        use_cache=False # Force re-render for test
    )

    if animation_path:
        logger.info(f"--- Manim Layout Test Successful ---")
        logger.info(f"Test animation generated: {animation_path}")
        print(f"\nTest animation generated successfully:")
        print(f"Output file: {animation_path}")
        print("Please review this video file to check the layout (content left, visual right).")
    else:
        logger.error("--- Manim Layout Test Failed ---")
        print("\nFailed to generate test animation.")
