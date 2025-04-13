import os
import logging
import subprocess
import tempfile
import shutil
from typing import Optional, List, Dict, Any
from pathlib import Path
import re
import hashlib # For caching
import json # For hashing complex data structures

from src.utils import ensure_dir_exists, logger

# Manim configuration - UPDATED
MANIM_QUALITY = "low_quality" # Keep low for faster testing, maybe change later
MANIM_FRAME_RATE = 24
MANIM_RENDERER = "cairo"
MANIM_BACKGROUND_COLOR = "#121212" # Dark theme background
MANIM_TEXT_COLOR = "#f0f0f0" # Off-white text
MANIM_HIGHLIGHT_COLOR = "#ffff00" # Yellow for highlight/markings
MANIM_TITLE_COLOR = "#ffffff" # White for titles
MANIM_EQUATION_COLOR = "#ffd700" # Yellow for equations
MANIM_TITLE_FONT = "Inter" # Use Inter font
MANIM_CONTENT_FONT = "Inter" # Use Inter font
MANIM_DEFAULT_FALLBACK_FONT = "Sans" # Fallback if Inter isn't found
BOX_EQUATIONS = False # Set to False as equations will be colored yellow

# Cache directory for rendered animations
ANIMATION_CACHE_DIR = Path(__file__).parent.parent / "assets" / "cache" / "manim_renders"

def check_manim_exists() -> bool:
    """Checks if the Manim command exists."""
    venv_manim_path = str(Path(__file__).parent.parent / ".venv" / "bin" / "manim")
    manim_cmd = venv_manim_path if Path(venv_manim_path).is_file() else "manim"
    found_path = shutil.which(manim_cmd)
    if found_path:
        if globals().get('MANIM_EXECUTABLE_PATH') != found_path:
             logger.info(f"Found Manim executable at: {found_path}")
             globals()['MANIM_EXECUTABLE_PATH'] = found_path
        return True
    else:
        logger.error(f"Manim command ('{manim_cmd}') not found in venv or PATH.")
        return False

MANIM_EXECUTABLE_PATH = "manim"

def parse_manim_output_path(stdout: str) -> Optional[str]:
    """Parses Manim's stdout to find the final output file path."""
    match = re.search(r"File ready at\s+'([^']+)'", stdout)
    if match: path = match.group(1); logger.info(f"Parsed Manim output path: {path}"); return path
    logger.warning("Could not parse output file path from Manim stdout."); return None

def _calculate_cache_key(section_index: int, timed_elements: List[Dict[str, Any]], diagram_path: Optional[str], audio_duration: float) -> str:
    """Calculates a unique hash key based on the inputs that affect the animation."""
    hasher = hashlib.sha256()
    hasher.update(str(section_index).encode('utf-8'))
    hasher.update(json.dumps(timed_elements, sort_keys=True).encode('utf-8'))
    hasher.update((diagram_path or "no_diagram").encode('utf-8'))
    hasher.update(f"{audio_duration:.3f}".encode('utf-8'))
    # Include relevant Manim config settings that might change
    hasher.update(MANIM_QUALITY.encode('utf-8'))
    hasher.update(MANIM_TITLE_FONT.encode('utf-8'))
    hasher.update(MANIM_CONTENT_FONT.encode('utf-8'))
    hasher.update(MANIM_BACKGROUND_COLOR.encode('utf-8'))
    hasher.update(MANIM_TEXT_COLOR.encode('utf-8'))
    hasher.update(MANIM_HIGHLIGHT_COLOR.encode('utf-8'))
    hasher.update(MANIM_TITLE_COLOR.encode('utf-8'))
    hasher.update(MANIM_EQUATION_COLOR.encode('utf-8'))
    hasher.update(str(BOX_EQUATIONS).encode('utf-8'))
    # Add font sizes? Might be overkill unless they change often via config
    return hasher.hexdigest()

# UPDATED function signature: removed segment_durations
def generate_animation_scene(
    section_index: int,
    timed_elements: List[Dict[str, Any]],
    diagram_path: Optional[str], # Path to PNG (diagram or chart)
    audio_duration: float, # Total duration including silence
    output_dir: str,
    temp_dir: str,
    use_cache: bool = True
) -> Optional[str]:
    """
    Generates Manim scene, timing animations based on total audio duration.
    Includes optional caching to reuse previously rendered animations.
    Handles text, LaTeX (equations), and diagrams/charts (as ImageMobjects).
    Applies updated styling (colors, fonts, layout).
    """
    logger.info(f"Generating Manim animation for section {section_index} (Syncing to total duration)")
    ensure_dir_exists(output_dir); ensure_dir_exists(temp_dir)
    ensure_dir_exists(str(ANIMATION_CACHE_DIR))

    # --- Caching Logic ---
    cache_key = _calculate_cache_key(section_index, timed_elements, diagram_path, audio_duration)
    cached_file_path = ANIMATION_CACHE_DIR / f"{cache_key}_section_{section_index}.mp4"
    final_output_filename = f"section_{section_index}_animation.mp4"
    final_output_filepath = os.path.join(output_dir, final_output_filename)

    if use_cache and cached_file_path.exists():
        try:
            shutil.copyfile(cached_file_path, final_output_filepath)
            logger.info(f"Using cached animation for section {section_index} (Key: {cache_key[:8]}...). Copied to {final_output_filepath}")
            return final_output_filepath
        except Exception as e:
            logger.warning(f"Failed to copy cached animation for section {section_index}: {e}. Will re-render.")
            try: cached_file_path.unlink(missing_ok=True)
            except OSError: pass
    # --- End Caching Logic ---

    if not timed_elements:
         logger.warning(f"No timed elements provided for section {section_index}. Skipping animation.")
         return None

    if not check_manim_exists(): return None

    timed_elements_repr = repr(timed_elements)
    actual_diagram_path_repr = repr(diagram_path) # Path to the PNG (diagram or chart)
    target_duration_val = audio_duration
    background_color_val = MANIM_BACKGROUND_COLOR
    frame_rate_val = MANIM_FRAME_RATE
    text_color_val = MANIM_TEXT_COLOR
    title_color_val = MANIM_TITLE_COLOR
    highlight_color_val = MANIM_HIGHLIGHT_COLOR
    equation_color_val = MANIM_EQUATION_COLOR # Pass equation color
    title_font_val = MANIM_TITLE_FONT
    content_font_val = MANIM_CONTENT_FONT
    fallback_font_val = MANIM_DEFAULT_FALLBACK_FONT
    box_equations_val = BOX_EQUATIONS # Pass updated value

    # Construct the script content using an f-string - Layout gap increased
    scene_script_content = f"""
# -*- coding: utf-8 -*-
from manim import *
import math
import sys
import os # Needed for checking diagram path

# Manim configuration
config.background_color = "{background_color_val}"
config.frame_rate = {frame_rate_val}
config.pixel_height = 1080
config.pixel_width = 1920

class GeneratedScene(Scene):
    def construct(self):
        # --- Parameters ---
        timed_elements = {timed_elements_repr}
        diagram_path_param = {actual_diagram_path_repr}
        target_duration = {target_duration_val}
        text_color = "{text_color_val}"
        title_color = "{title_color_val}"
        highlight_color = "{highlight_color_val}" # Red for highlights/pointers
        equation_color = "{equation_color_val}" # Yellow for equations
        title_font = "{title_font_val}"
        content_font = "{content_font_val}"
        fallback_font = "{fallback_font_val}"
        box_equations = {box_equations_val} # Should be False now
        # --- End Parameters ---

        # --- Dynamic Layout & Style Parameters ---
        screen_width = config.frame_width
        screen_height = config.frame_height
        has_diagram = diagram_path_param and os.path.exists(diagram_path_param)

        if has_diagram:
            # Layout when diagram IS present
            content_area_width_ratio = 0.45 # Smaller text area
            diagram_area_width_ratio = 0.45 # Larger diagram area
            horizontal_gap_ratio = 0.10
            content_font_size = 42 # Smaller content font
            equation_font_size = 46 # Smaller equation font
            print("MANIM_SCENE_INFO: Using layout with diagram.", file=sys.stderr)
        else:
            # Default layout when NO diagram is present
            content_area_width_ratio = 0.90 # Wider text area
            diagram_area_width_ratio = 0.0 # No diagram area needed
            horizontal_gap_ratio = 0.10
            content_font_size = 48 # Default content font
            equation_font_size = 52 # Default equation font
            print("MANIM_SCENE_INFO: Using layout without diagram.", file=sys.stderr)

        # Shared parameters
        title_font_size = 72
        vertical_buff = 0.55
        title_content_buff = 0.7
        title_top_buff = 0.5

        # Calculate widths and positions based on chosen ratios
        content_area_width = screen_width * content_area_width_ratio
        diagram_area_width = screen_width * diagram_area_width_ratio
        horizontal_gap = screen_width * horizontal_gap_ratio

        content_area_left_edge = -screen_width / 2 + 0.6 # Keep buffer from left edge
        if has_diagram:
            diagram_area_right_edge = screen_width / 2 - 0.2
            diagram_area_left_edge = diagram_area_right_edge - diagram_area_width
            content_area_right_edge = diagram_area_left_edge - horizontal_gap
        else:
            # If no diagram, content can go further right
            content_area_right_edge = screen_width / 2 - 0.6

        # Spacing (remains the same)
        vertical_buff = 0.55
        title_content_buff = 0.7
        title_top_buff = 0.5

        # --- Create Mobjects ---
        mobjects_dict = {{}}
        element_data = {{}}
        text_mobjects_list = []

        title_mobject = None
        diagram_mobject = None
        start_index = 0

        # Create Title
        if timed_elements and timed_elements[0].get('type') == 'text':
             try:
                 title_text = timed_elements[0].get('content', 'Section')
                 try:
                     title_mobject = Text(title_text, font_size=title_font_size, color=title_color, weight=BOLD, font=title_font)
                 except Exception:
                      print(f"MANIM_SCENE_WARNING: Title font '{{title_font}}' not found. Using fallback '{{fallback_font}}'.", file=sys.stderr)
                      title_mobject = Text(title_text, font_size=title_font_size, color=title_color, weight=BOLD, font=fallback_font)

                 if title_mobject.width > (screen_width - 1.0):
                     title_mobject.scale_to_fit_width(screen_width - 1.0)

                 title_mobject.to_edge(UP, buff=title_top_buff)
                 mobjects_dict[0] = title_mobject
                 element_data[0] = timed_elements[0]
                 start_index = 1
             except Exception as e:
                  print(f"MANIM_SCENE_ERROR: Failed to create title: {{e}}", file=sys.stderr)
                  title_mobject = None

        # Create Text/Latex Mobjects and Diagram Mobject
        for i in range(start_index, len(timed_elements)):
            element = timed_elements[i]
            content = element.get("content", "")
            element_type = element.get("type", "text")
            mobject = None
            is_diagram_element = False
            try:
                if element_type == "text":
                     try:
                         point = Text(content, font_size=content_font_size, color=text_color, font=content_font)
                     except Exception:
                         print(f"MANIM_SCENE_WARNING: Content font '{{content_font}}' not found. Using fallback '{{fallback_font}}'.", file=sys.stderr)
                         point = Text(content, font_size=content_font_size, color=text_color, font=fallback_font)

                     # Scale first to fit width constraint
                     if point.width > content_area_width:
                         point.scale_to_fit_width(content_area_width)
                     text_mobjects_list.append(point)
                     mobject = point

                elif element_type == "latex":
                     try:
                         latex_mobject = MathTex(content, font_size=equation_font_size).set_color(equation_color)
                         mobject = latex_mobject
                         # Scale first
                         if mobject.width > content_area_width:
                             mobject.scale_to_fit_width(content_area_width)
                         text_mobjects_list.append(mobject)
                     except Exception as latex_err:
                          print(f"MANIM_SCENE_ERROR: Failed to render LaTeX for element {{i}}: {{content}}. Is LaTeX installed? Error: {{latex_err}}", file=sys.stderr)
                          mobject = None

                elif element_type in ["diagram", "chart_data"]:
                     is_diagram_element = True
                     if diagram_path_param and not diagram_mobject:
                         if os.path.exists(diagram_path_param):
                             try:
                                 diagram_mobject = ImageMobject(diagram_path_param)
                                 # Scale diagram here before layout
                                 diagram_mobject.scale_to_fit_width(diagram_area_width)
                                 available_height = screen_height - (title_mobject.height if title_mobject else 0) - title_top_buff - 1.0
                                 if diagram_mobject.height > available_height:
                                      diagram_mobject.scale_to_fit_height(available_height)
                                 mobject = diagram_mobject
                             except Exception as img_err:
                                 print(f"MANIM_SCENE_ERROR: Failed to load diagram/chart image '{{diagram_path_param}}': {{img_err}}", file=sys.stderr)
                                 diagram_mobject = None
                                 mobject = None
                         else:
                             print(f"MANIM_SCENE_WARNING: Diagram/chart path '{{diagram_path_param}}' not found.", file=sys.stderr)
                             mobject = None
                     else:
                         mobject = None

                mobjects_dict[i] = diagram_mobject if is_diagram_element and diagram_mobject else mobject
                element_data[i] = element

            except Exception as e:
                 print(f"MANIM_SCENE_ERROR: Failed to process mobject for element {{i}}: {{element}}. Error: {{e}}", file=sys.stderr)


        # --- Layout (Spacing and overlap checks) ---
        content_vg = VGroup(*text_mobjects_list)
        if len(content_vg) > 0:
            content_vg.arrange(DOWN, aligned_edge=LEFT, buff=vertical_buff)
            ref_point = title_mobject if title_mobject else Dot().to_edge(UP)
            content_vg.next_to(ref_point, DOWN, buff=title_content_buff)
            content_vg.align_to([content_area_left_edge, 0, 0], LEFT)

            # Check if content exceeds right boundary after alignment
            if content_vg.get_right()[0] > content_area_right_edge:
                 print(f"MANIM_SCENE_WARNING: Content VGroup potentially exceeds its allocated width. Right edge: {{content_vg.get_right()[0]:.2f}}, Boundary: {{content_area_right_edge:.2f}}", file=sys.stderr)
                 # Force scale again if it somehow exceeded width after arrangement
                 content_vg.scale_to_fit_width(content_area_width)
                 content_vg.align_to([content_area_left_edge, 0, 0], LEFT) # Re-align after scaling

            # Vertical adjustment
            if content_vg.get_bottom()[1] < -screen_height/2 + 0.5:
                 content_vg.scale_to_fit_height(screen_height - (title_mobject.height if title_mobject else 0) - title_top_buff - 1.0)
                 content_vg.next_to(ref_point, DOWN, buff=title_content_buff)
                 content_vg.align_to([content_area_left_edge, 0, 0], LEFT)


        # Layout Diagram/Chart on the Right
        if diagram_mobject:
            # Scaling was done during creation
            # Position diagram: Align its LEFT edge to the diagram_area_left_edge
            diagram_mobject.align_to([diagram_area_left_edge, 0, 0], LEFT)

            # Align vertically
            if len(content_vg) > 0:
                 diagram_mobject.align_to(content_vg, UP)
            elif title_mobject:
                 diagram_mobject.next_to(title_mobject, DOWN, buff=title_content_buff)
                 diagram_mobject.align_to([diagram_area_left_edge, 0, 0], LEFT)
            else:
                 diagram_mobject.center().align_to([diagram_area_left_edge, 0, 0], LEFT)

            # Overlap check (more strict)
            if len(content_vg) > 0 and diagram_mobject.get_left()[0] < content_vg.get_right()[0] + horizontal_gap * 0.8: # Check against 80% of gap
                 print(f"MANIM_SCENE_WARNING: Potential overlap detected. Diagram left: {{diagram_mobject.get_left()[0]:.2f}}, Content right: {{content_vg.get_right()[0]:.2f}}, Gap: {{horizontal_gap:.2f}}", file=sys.stderr)


        # --- Calculate Approximate Timing ---
        num_animatable_elements = len(text_mobjects_list) + (1 if diagram_mobject else 0)
        available_duration_for_elements = target_duration - 1.5 # Buffer
        if available_duration_for_elements < 1.0: available_duration_for_elements = 1.0
        duration_per_element = (available_duration_for_elements / num_animatable_elements) if num_animatable_elements > 0 else 1.0
        print(f"MANIM_SCENE_INFO: Approx duration per element: {{duration_per_element:.2f}}s ({{num_animatable_elements}} elements, {{target_duration:.2f}}s total)", file=sys.stderr)

        # --- Execute Animations ---
        current_time = 0.0
        active_highlight_mobject = None
        dehighlight_runtime = 0.2 # Define default value before loops

        # Animate Title
        if title_mobject:
             title_anim_duration = 0.7
             self.play(Write(title_mobject), run_time=title_anim_duration)
             current_time += title_anim_duration

        # Animate Text/Latex Elements Sequentially
        for point_mobject in text_mobjects_list:
            speech_duration = duration_per_element
            appear_runtime = 0.3
            highlight_runtime = 0.2
            dehighlight_runtime = 0.2

            # Dehighlight previous
            if active_highlight_mobject is not None:
                 original_color = text_color
                 if isinstance(active_highlight_mobject, MathTex):
                      original_color = equation_color
                 self.play(active_highlight_mobject.animate.set_color(original_color), run_time=dehighlight_runtime)
                 current_time += dehighlight_runtime
                 active_highlight_mobject = None

            # Appear
            self.play(FadeIn(point_mobject, shift=RIGHT*0.2), run_time=appear_runtime)
            current_time += appear_runtime

            # Highlight
            self.play(point_mobject.animate.set_color(highlight_color), run_time=highlight_runtime)
            current_time += highlight_runtime
            active_highlight_mobject = point_mobject

            # Wait
            adjusted_wait = max(0, speech_duration - appear_runtime - highlight_runtime - dehighlight_runtime)
            if adjusted_wait > 0.01:
                self.wait(adjusted_wait)
                current_time += adjusted_wait

        # Animate diagram (if exists) after all text/latex
        if diagram_mobject:
            speech_duration = duration_per_element
            appear_runtime = 0.5

            # Dehighlight last text/latex point
            if active_highlight_mobject is not None:
                 original_color = text_color
                 if isinstance(active_highlight_mobject, MathTex):
                      original_color = equation_color
                 self.play(active_highlight_mobject.animate.set_color(original_color), run_time=dehighlight_runtime)
                 current_time += dehighlight_runtime
                 active_highlight_mobject = None

            # Appear diagram
            self.play(FadeIn(diagram_mobject), run_time=appear_runtime)
            current_time += appear_runtime

            # Wait for remaining duration
            adjusted_wait = max(0, speech_duration - appear_runtime - dehighlight_runtime)
            if adjusted_wait > 0.01:
                self.wait(adjusted_wait)
                current_time += adjusted_wait

        # Dehighlight the very last active element
        if active_highlight_mobject is not None:
             original_color = text_color
             if isinstance(active_highlight_mobject, MathTex):
                  original_color = equation_color
             self.play(active_highlight_mobject.animate.set_color(original_color), run_time=dehighlight_runtime)
             current_time += dehighlight_runtime


        # Final wait
        final_wait = target_duration - current_time
        if final_wait > 0.01:
            self.wait(final_wait)
        elif final_wait < -0.1:
             print(f"MANIM_SCENE_WARNING: Total animation time ({{current_time:.2f}}s) exceeded target audio duration ({{target_duration:.2f}}s).", file=sys.stderr)

""" # End of f-string template

    temp_script_path = None
    temp_media_dir = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=temp_dir, delete=False, encoding='utf-8') as temp_script_file:
            temp_script_path = temp_script_file.name
            temp_script_file.write(scene_script_content)
        logger.info(f"Created temporary Manim script: {temp_script_path}")

        scene_name = "GeneratedScene"
        temp_media_dir = os.path.join(temp_dir, f"manim_media_{section_index}")
        ensure_dir_exists(temp_media_dir)

        command = [
            MANIM_EXECUTABLE_PATH,
            "--media_dir", temp_media_dir,
            "-q", MANIM_QUALITY[0], # Use first char of quality string (e.g., 'l' for low)
            temp_script_path,
            scene_name
        ]

        logger.info(f"Executing Manim command: {' '.join(command)}")
        result = None
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=600, encoding='utf-8', errors='replace')
        except subprocess.TimeoutExpired:
            logger.error(f"Manim rendering timed out for section {section_index} after 600 seconds.")
            return None
        except Exception as subproc_err:
             logger.error(f"Error running Manim subprocess for section {section_index}: {subproc_err}")
             return None

        actual_manim_output_file = None
        if result and result.returncode == 0:
            actual_manim_output_file = parse_manim_output_path(result.stdout)
            if actual_manim_output_file and Path(actual_manim_output_file).exists():
                logger.info(f"Manim render successful for section {section_index}.")
                try:
                    shutil.move(actual_manim_output_file, final_output_filepath)
                    logger.info(f"Moved rendered animation to: {final_output_filepath}")
                    if use_cache:
                        try:
                            shutil.copyfile(final_output_filepath, cached_file_path)
                            logger.info(f"Copied animation to cache: {cached_file_path}")
                        except Exception as cache_copy_err:
                            logger.warning(f"Failed to copy animation to cache: {cache_copy_err}")
                    return final_output_filepath
                except Exception as move_err:
                    logger.error(f"Failed to move Manim output file {actual_manim_output_file} to {final_output_filepath}: {move_err}")
                    return None
            else:
                 logger.error(f"Manim reported success, but couldn't find/parse output file from stdout.")
                 logger.error(f"Manim Stdout:\n{result.stdout}")
                 logger.error(f"Manim Stderr:\n{result.stderr}")
                 return None
        else:
            logger.error(f"Manim rendering failed for section {section_index} (Return Code: {result.returncode if result else 'N/A'})")
            if result:
                 logger.error(f"--- Manim Full Stdout ---\n{result.stdout}\n------------------------")
                 logger.error(f"--- Manim Full Stderr ---\n{result.stderr}\n------------------------")
            return None

    except Exception as e:
        logger.error(f"An unexpected error occurred during animation generation setup/execution for section {section_index}: {e}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return None
    finally:
        if temp_script_path and os.path.exists(temp_script_path):
            try:
                os.remove(temp_script_path)
                logger.info(f"Cleaned up temporary script: {temp_script_path}")
            except OSError as e:
                logger.warning(f"Failed to clean up temporary script {temp_script_path}: {e}")
        if temp_media_dir and os.path.exists(temp_media_dir):
             try:
                 shutil.rmtree(temp_media_dir)
                 logger.info(f"Cleaned up temporary media directory: {temp_media_dir}")
             except OSError as e:
                 logger.warning(f"Failed to clean up temporary media directory {temp_media_dir}: {e}")

# Example usage for testing layout and element handling
if __name__ == '__main__':
    print("Testing Animation Generation Layout...")

    # Define test directories relative to this script's location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    test_output_dir = project_root / "output" / "test_layout"
    test_temp_dir = project_root / "assets" / "temp_test" # Use a subfolder in assets/temp
    test_diagrams_dir = project_root / "assets" / "diagrams_test" # Separate dir for test diagrams

    ensure_dir_exists(str(test_output_dir))
    ensure_dir_exists(str(test_temp_dir))
    ensure_dir_exists(str(test_diagrams_dir))

    print(f"Test Output dir: {test_output_dir}")
    print(f"Test Temp dir: {test_temp_dir}")
    print(f"Test Diagrams dir: {test_diagrams_dir}")

    # Create dummy diagram and chart files if they don't exist
    dummy_diagram_path = test_diagrams_dir / "dummy_diagram.png"
    dummy_chart_path = test_diagrams_dir / "dummy_chart.png"
    created_dummy = False

    try:
        from PIL import Image, ImageDraw, ImageFont
        pil_available = True
    except ImportError:
        pil_available = False
        print("WARNING: Pillow not installed. Cannot create dummy images for testing. Set test_diagram_path manually if needed.")

    if pil_available:
        if not dummy_diagram_path.exists():
            try:
                img = Image.new('RGB', (800, 600), color = '#444444')
                d = ImageDraw.Draw(img)
                # Use a basic system font if possible, otherwise default
                try: font = ImageFont.truetype("sans-serif.ttf", 40)
                except IOError: font = ImageFont.load_default()
                d.text((10,10), "Dummy Diagram", fill=(255,255,0), font=font)
                img.save(dummy_diagram_path)
                print(f"Created dummy diagram: {dummy_diagram_path}")
                created_dummy = True
            except Exception as e: print(f"Error creating dummy diagram: {e}")

        if not dummy_chart_path.exists():
             try:
                 img = Image.new('RGB', (800, 600), color = '#555555')
                 d = ImageDraw.Draw(img)
                 try: font = ImageFont.truetype("sans-serif.ttf", 40)
                 except IOError: font = ImageFont.load_default()
                 d.text((10,10), "Dummy Chart", fill=(0,255,255), font=font)
                 img.save(dummy_chart_path)
                 print(f"Created dummy chart: {dummy_chart_path}")
                 created_dummy = True
             except Exception as e: print(f"Error creating dummy chart: {e}")

    # --- Test Case 1: Layout WITH Diagram ---
    print(f"\n--- Running Layout Test WITH Diagram (Section 888) ---")
    test_timed_elements_with_diagram = [
        {"type": "text", "content": "Test Title (With Diagram)", "start_time": 0, "end_time": 2},
        {"type": "text", "content": "This text should be smaller.", "start_time": 2, "end_time": 5},
        {"type": "latex", "content": r"E = mc^2", "start_time": 5, "end_time": 8}, # Equation should also be smaller
        {"type": "text", "content": "More text points to check density.", "start_time": 8, "end_time": 11},
        {"type": "text", "content": "Another text point.", "start_time": 11, "end_time": 14},
        {"type": "diagram", "content": "diagram_placeholder", "start_time": 14, "end_time": 20} # Diagram appears last
    ]
    test_diagram_path_with_diagram = str(dummy_diagram_path) if dummy_diagram_path.exists() else None
    test_audio_duration_with_diagram = 22.0

    animation_path_with_diagram = generate_animation_scene(
        section_index=888, # Use a distinct index for test output
        timed_elements=test_timed_elements_with_diagram,
        diagram_path=test_diagram_path_with_diagram,
        audio_duration=test_audio_duration_with_diagram,
        output_dir=str(test_output_dir), # Pass as string
        temp_dir=str(test_temp_dir),     # Pass as string
        use_cache=False # Disable cache for test run
    )

    if animation_path_with_diagram:
        print(f"\nSuccessfully generated layout test animation WITH diagram: {animation_path_with_diagram}")
        print(f"Please check video 888 for smaller text and larger diagram.")
    else:
        print("\nFailed to generate layout test animation WITH diagram.")


    # --- Test Case 2: Layout WITHOUT Diagram ---
    print(f"\n--- Running Layout Test WITHOUT Diagram (Section 777) ---")
    test_timed_elements_no_diagram = [
        {"type": "text", "content": "Test Title (No Diagram)", "start_time": 0, "end_time": 2},
        {"type": "text", "content": "This text should use the default larger font size.", "start_time": 2, "end_time": 6},
        {"type": "latex", "content": r"A = \pi r^2", "start_time": 6, "end_time": 10}, # Equation should be default size
        {"type": "text", "content": "More text content filling the wider space.", "start_time": 10, "end_time": 14},
        {"type": "text", "content": "Final text point.", "start_time": 14, "end_time": 18},
    ]
    test_audio_duration_no_diagram = 20.0

    animation_path_no_diagram = generate_animation_scene(
        section_index=777, # Use a different index
        timed_elements=test_timed_elements_no_diagram,
        diagram_path=None, # Explicitly pass None for diagram path
        audio_duration=test_audio_duration_no_diagram,
        output_dir=str(test_output_dir),
        temp_dir=str(test_temp_dir),
        use_cache=False
    )

    if animation_path_no_diagram:
        print(f"\nSuccessfully generated layout test animation WITHOUT diagram: {animation_path_no_diagram}")
        print(f"Please check video 777 for default text size and layout.")
    else:
        print("\nFailed to generate layout test animation WITHOUT diagram.")
