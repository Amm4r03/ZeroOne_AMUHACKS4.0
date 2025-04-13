import os
from PIL import Image, ImageDraw, ImageFont
from edu_video_generator.src.utils import ensure_dir_exists # Use existing utility

TEMP_DIR = os.path.join(os.path.dirname(__file__), "assets", "temp")
OUTPUT_PATH = os.path.join(TEMP_DIR, "dummy_visual.png")
IMAGE_WIDTH = 800
IMAGE_HEIGHT = 600
BG_COLOR = (40, 40, 40) # Dark grey
TEXT_COLOR = (240, 240, 240) # Off-white

if __name__ == "__main__":
    try:
        ensure_dir_exists(TEMP_DIR)
        img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Try to load a font, fallback to default
        try:
            # Adjust path if needed, or use a common system font
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()
            print("Arial font not found, using default font.")

        text = "Dummy Visual\n(Diagram/Chart)"
        # Calculate text position
        # Use textbbox for better centering estimation
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (IMAGE_WIDTH - text_width) / 2
        text_y = (IMAGE_HEIGHT - text_height) / 2

        draw.text((text_x, text_y), text, fill=TEXT_COLOR, font=font, align="center")
        img.save(OUTPUT_PATH)
        print(f"Successfully created dummy visual element at: {OUTPUT_PATH}")

    except ImportError:
        print("Error: Pillow library is not installed. Cannot create dummy image.")
        print("Please install it: pip install Pillow")
    except Exception as e:
        print(f"An error occurred creating the dummy image: {e}")
