import soundfile as sf
import time
import os
import torch # needed for potential voice tensor loading

# Import Kokoro pipeline
try:
    from kokoro import KPipeline
except ImportError:
    print("ERROR: Failed to import KPipeline from kokoro. Make sure 'kokoro' is installed correctly.")
    exit(1)

# --- Configuration ---
OUTPUT_FILENAME = "kokoro_test_output.wav"
# Use American English ('a') as per the example, can be changed
LANGUAGE_CODE = 'a'
# Use a default voice from the example, can be changed
VOICE = 'af_heart'
# Save in the project root
PROJECT_BASE_DIR = os.path.dirname(__file__)
OUTPUT_PATH = os.path.join(PROJECT_BASE_DIR, OUTPUT_FILENAME)

# --- Main Test Logic ---
def test_kokoro_tts():
    print(f"Initializing Kokoro pipeline with lang_code='{LANGUAGE_CODE}'...")
    try:
        # Initialize the pipeline
        # Note: This might download model files on first run
        pipeline = KPipeline(lang_code=LANGUAGE_CODE)
        print("Kokoro pipeline initialized successfully.")
    except Exception as e:
        print(f"Error initializing Kokoro pipeline: {e}")
        import traceback
        traceback.print_exc()
        return

    # Sample text to synthesize
    text = "Hello, this is a test of the Kokoro text-to-speech model using its dedicated library."
    print(f"Synthesizing text: '{text}'")
    print(f"Using voice: '{VOICE}'")

    try:
        # Generate audio using the pipeline
        # The pipeline returns a generator; we'll just take the first result for this simple test
        start_time = time.time()
        generator = pipeline(text, voice=VOICE, speed=1) # speed=1 is default

        # Get the first (and likely only) audio chunk from the generator
        # The generator yields tuples: (graphemes, phonemes, audio_numpy_array)
        _gs, _ps, audio_data = next(generator)
        end_time = time.time()

        print(f"Waveform generation took {end_time - start_time:.2f} seconds.")

        # Get sampling rate (Kokoro default is 24000 Hz)
        sampling_rate = 24000
        print(f"Using sampling rate: {sampling_rate}")

        # Save the audio file
        print(f"Saving audio to: {OUTPUT_PATH}")
        sf.write(OUTPUT_PATH, audio_data, sampling_rate)
        print("Audio saved successfully.")

    except StopIteration:
         print("Error: The pipeline generator did not yield any audio data.")
    except Exception as e:
        print(f"Error during synthesis or saving: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kokoro_tts()
