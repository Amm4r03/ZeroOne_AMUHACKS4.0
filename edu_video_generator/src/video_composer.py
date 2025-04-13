import os
import logging
from typing import List, Dict, Optional
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
from moviepy.video.VideoClip import ColorClip
from moviepy.audio.AudioClip import AudioArrayClip
import numpy as np

from src.utils import ensure_dir_exists, logger

# --- Configuration ---
VIDEO_FPS = 24
VIDEO_CODEC = "libx264" # Standard H.264 codec
AUDIO_CODEC = "aac"     # Standard AAC codec

def compose_final_video(section_assets: List[Dict[str, Optional[str]]], output_filepath: str) -> bool:
    """
    Composes the final video by concatenating section animations and adding audio.

    Args:
        section_assets: A list of dictionaries, where each dictionary represents a section
                        and contains keys 'animation_path' (path to the Manim MP4)
                        and 'audio_path' (path to the MP3 audio file). Paths can be None
                        if generation failed for that asset.
        output_filepath: The full path for the final output MP4 video file.

    Returns:
        True if the video composition was successful, False otherwise.
    """
    logger.info(f"Starting final video composition for: {output_filepath}")
    ensure_dir_exists(os.path.dirname(output_filepath))

    final_clips = []
    clips_to_close = [] # Keep track of clips to close manually

    try:
        for i, assets in enumerate(section_assets):
            logger.info(f"Processing section {i} for composition...")
            animation_path = assets.get('animation_path')
            audio_path = assets.get('audio_path')

            if not animation_path or not os.path.exists(animation_path):
                logger.error(f"Animation video file missing for section {i}. Expected at: {animation_path}. Skipping section.")
                continue # Skip this section if animation is missing

            if not audio_path or not os.path.exists(audio_path):
                logger.error(f"Audio file missing for section {i}. Expected at: {audio_path}. Skipping section.")
                continue # Skipping section if audio is missing

            try:
                # Load video and audio clips
                video_clip = VideoFileClip(animation_path)
                audio_clip = AudioFileClip(audio_path)
                clips_to_close.extend([video_clip, audio_clip]) # Add to list for closing

                # Basic duration check (optional but recommended)
                if abs(video_clip.duration - audio_clip.duration) > 0.1: # Allow 100ms difference
                    logger.warning(f"Duration mismatch for section {i}: "
                                   f"Video={video_clip.duration:.2f}s, Audio={audio_clip.duration:.2f}s. "
                                   f"Using video duration.")
                    # Trim the longer one or decide on a strategy. Using video duration is simplest.
                    # audio_clip = audio_clip.subclip(0, video_clip.duration) # Example: Trim audio
                    # Or trim video: video_clip = video_clip.subclip(0, audio_clip.duration)

                # Assign the audio clip to the video clip's audio attribute
                video_clip.audio = audio_clip
                # The video_clip object itself is now modified

                final_clips.append(video_clip) # Append the modified video_clip
                logger.info(f"Successfully processed section {i}.")

            except Exception as e:
                logger.error(f"Error processing clips for section {i} (Video: {animation_path}, Audio: {audio_path}): {e}")
                # Decide whether to skip this section or halt the process
                continue # Skip faulty section

        if not final_clips:
            logger.error("No valid sections were processed. Cannot create final video.")
            return False

        # Concatenate all processed clips
        logger.info(f"Concatenating {len(final_clips)} processed section clips...")
        final_video = concatenate_videoclips(final_clips, method="compose") # 'compose' is often more robust
        clips_to_close.append(final_video) # Add final video for closing

        # Write the final video file
        logger.info(f"Writing final video to {output_filepath}...")
        final_video.write_videofile(
            output_filepath,
            fps=VIDEO_FPS,
            codec=VIDEO_CODEC,
            audio_codec=AUDIO_CODEC,
            threads=4, # Use 4 threads for potentially faster encoding
            preset='fast', # Use a faster encoding preset (might slightly reduce quality)
            logger=None # Suppress moviepy progress bar if desired
        )

        logger.info(f"Successfully composed final video: {output_filepath}")
        return True

    except Exception as e:
        logger.error(f"An error occurred during final video composition: {e}")
        return False
    finally:
        # --- Crucial: Close all opened clips ---
        logger.info(f"Closing {len(clips_to_close)} MoviePy clips...")
        for clip in clips_to_close:
            try:
                clip.close()
            except Exception as close_err:
                # Log error but continue closing others
                logger.warning(f"Error closing a MoviePy clip: {close_err}")
        logger.info("Finished closing clips.")


# Example usage
if __name__ == '__main__':
    print("Testing Video Composition...")
    # This example requires dummy video and audio files to exist.
    # You would typically run the previous steps first to generate these.

    base_dir = os.path.dirname(__file__)
    assets_dir = os.path.join(base_dir, '..', 'assets')
    output_dir = os.path.join(base_dir, '..', 'output')
    ensure_dir_exists(output_dir)

    # Create dummy assets for testing (replace with actual generated paths)
    dummy_anim_dir = os.path.join(assets_dir, 'manim_videos')
    dummy_audio_dir = os.path.join(assets_dir, 'audio')
    ensure_dir_exists(dummy_anim_dir)
    ensure_dir_exists(dummy_audio_dir)

    test_assets = []
    files_created = True
    try:
        # Create dummy 2-second black video with silent audio
        from moviepy.editor import ColorClip, AudioArrayClip
        import numpy as np
        duration = 2.0
        fps = VIDEO_FPS
        size = (100, 100) # Small size for quick test
        sr = 44100 # Sample rate for audio

        for i in range(2): # Create 2 dummy sections
            anim_path = os.path.join(dummy_anim_dir, f"dummy_anim_{i}.mp4")
            audio_path = os.path.join(dummy_audio_dir, f"dummy_audio_{i}.mp3")

            # Create dummy video
            clip = ColorClip(size=size, color=(0,0,0), duration=duration)
            clip.write_videofile(anim_path, fps=fps, logger=None)
            clip.close()

            # Create dummy silent audio
            silence = np.zeros((int(sr * duration), 2)) # Stereo silence
            audio_clip = AudioArrayClip(silence, fps=sr)
            audio_clip.write_audiofile(audio_path, fps=sr, codec='mp3', logger=None)
            audio_clip.close()

            test_assets.append({'animation_path': anim_path, 'audio_path': audio_path})
            print(f"Created dummy asset {i}: Video={anim_path}, Audio={audio_path}")

    except ImportError:
        print("MoviePy needed to create dummy files for testing.")
        files_created = False
    except Exception as e:
        print(f"Error creating dummy files: {e}")
        files_created = False

    if files_created and test_assets:
        test_output_file = os.path.join(output_dir, "test_composition.mp4")
        print(f"\nAttempting composition to: {test_output_file}")

        success = compose_final_video(test_assets, test_output_file)

        if success:
            print(f"\nSuccessfully composed test video: {test_output_file}")
            # Verify duration
            try:
                with VideoFileClip(test_output_file) as final_clip:
                     print(f"  Final Duration: {final_clip.duration:.2f}s (Expected approx {duration * len(test_assets):.2f}s)")
            except Exception as e:
                 print(f"  Could not verify duration: {e}")
            # Clean up test output
            # os.remove(test_output_file)
            # print(f"  Cleaned up test output file.")
        else:
            print("\nFailed to compose test video.")

        # Clean up dummy assets
        print("Cleaning up dummy assets...")
        for assets in test_assets:
            for path in [assets.get('animation_path'), assets.get('audio_path')]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError as e:
                        print(f"  Warning: Failed to remove {path}: {e}")
    else:
        print("\nSkipping composition test as dummy files could not be created.")
