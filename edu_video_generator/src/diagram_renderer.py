import os
import logging
import subprocess
import tempfile
import shutil
import json # Added for parsing chart data
from typing import Optional, Dict, Any
from dotenv import load_dotenv

try:
    import matplotlib
    matplotlib.use('Agg') # Use non-interactive backend suitable for scripts
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None # Define plt as None if import fails

from src.utils import ensure_dir_exists, logger

# Load environment variables from .env file located in ../config relative to this script
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Configuration ---
MERMAID_CLI_PATH = os.getenv("MERMAID_CLI_PATH", "mmdc") # Default to 'mmdc' if not set in .env
DEFAULT_WIDTH = 1920 # For Mermaid rendering
DEFAULT_HEIGHT = 1080 # For Mermaid rendering
DEFAULT_THEME = "neutral" # Mermaid theme
DEFAULT_BG_COLOR = "transparent" # Mermaid background

# Chart Styling Configuration
CHART_BG_COLOR = "#121212"
CHART_TEXT_COLOR = "#f0f0f0"
CHART_TITLE_COLOR = "#ffffff"
CHART_PRIMARY_COLOR = "#ffd700" # Yellow for bars/lines
CHART_SECONDARY_COLOR = "#ff4c4c" # Red for accents if needed
CHART_FONT_FAMILY = "Inter" # Match Manim font
CHART_FONT_SIZE_TITLE = 18
CHART_FONT_SIZE_LABEL = 14
CHART_FONT_SIZE_TICKS = 14 # Increased tick label size for visibility
CHART_DPI = 150 # Higher DPI for better quality PNG

def check_mmdc_exists(mmdc_path: str) -> bool:
    """Checks if the Mermaid CLI command exists."""
    if shutil.which(mmdc_path):
        logger.info(f"Found Mermaid CLI executable at: {shutil.which(mmdc_path)}")
        return True
    else:
        logger.error(f"Mermaid CLI ('{mmdc_path}') not found in PATH or specified location.")
        logger.error("Please install @mermaid-js/mermaid-cli globally (`npm install -g @mermaid-js/mermaid-cli`) or set MERMAID_CLI_PATH in .env")
        return False

def _render_mermaid_diagram(section_index: int, mermaid_code: str, output_filepath: str, temp_dir: str) -> bool:
    """Internal function to render Mermaid code to PNG."""
    if not check_mmdc_exists(MERMAID_CLI_PATH):
        return False

    temp_mmd_filepath = None
    try:
        # Ensure code is stripped before writing
        cleaned_mermaid_code = mermaid_code.strip()
        if not cleaned_mermaid_code:
             logger.warning(f"Mermaid code for section {section_index} is empty after stripping.")
             return False

        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', dir=temp_dir, delete=False, encoding='utf-8') as temp_mmd_file:
            temp_mmd_filepath = temp_mmd_file.name
            temp_mmd_file.write(f"%% Section {section_index} Diagram\n")
            temp_mmd_file.write(cleaned_mermaid_code) # Write cleaned code
        logger.info(f"Created temporary Mermaid file: {temp_mmd_filepath}")

        command = [
            MERMAID_CLI_PATH,
            "-i", temp_mmd_filepath,
            "-o", output_filepath,
            "-w", str(DEFAULT_WIDTH),
            "-H", str(DEFAULT_HEIGHT),
            "-t", DEFAULT_THEME,
            "-b", DEFAULT_BG_COLOR
        ]

        logger.info(f"Executing Mermaid CLI command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='replace')

        if result.returncode == 0:
            logger.info(f"Successfully rendered Mermaid diagram for section {section_index} to {output_filepath}")
            return True
        else:
            logger.error(f"Mermaid CLI failed for section {section_index} (Return Code: {result.returncode})")
            logger.error(f"Stderr: {result.stderr.strip()}")
            logger.error(f"Stdout: {result.stdout.strip()}")
            return False

    except Exception as e:
        logger.error(f"An unexpected error occurred during Mermaid rendering for section {section_index}: {e}")
        return False
    finally:
        if temp_mmd_filepath and os.path.exists(temp_mmd_filepath):
            try:
                os.remove(temp_mmd_filepath)
                logger.info(f"Cleaned up temporary Mermaid file: {temp_mmd_filepath}")
            except OSError as e:
                logger.warning(f"Failed to clean up temporary Mermaid file {temp_mmd_filepath}: {e}")

def _render_matplotlib_chart(section_index: int, chart_data: Dict[str, Any], output_filepath: str) -> bool:
    """Internal function to render chart data using Matplotlib."""
    if not MATPLOTLIB_AVAILABLE:
        logger.error("Matplotlib is not installed. Cannot render chart. Please install it (`pip install matplotlib`).")
        return False

    chart_type = chart_data.get("chart_type", "bar")
    labels = chart_data.get("labels", [])
    values = chart_data.get("values", [])
    title = chart_data.get("title")
    x_label = chart_data.get("x_axis_label") # Get optional x-axis label
    y_label = chart_data.get("y_axis_label") # Get optional y-axis label

    if not title:
        logger.error(f"Missing 'title' in chart_data for section {section_index}.")
        return False
    if not labels or not values or len(labels) != len(values):
        logger.error(f"Invalid chart data for section {section_index}: Labels/values mismatch or missing.")
        return False

    fig, ax = plt.subplots(figsize=(8, 6), dpi=CHART_DPI) # Adjust figsize as needed
    fig.patch.set_facecolor(CHART_BG_COLOR)
    ax.set_facecolor(CHART_BG_COLOR)

    # Apply styling
    plt.rcParams.update({
        'font.family': CHART_FONT_FAMILY,
        'font.size': CHART_FONT_SIZE_LABEL,
        'text.color': CHART_TEXT_COLOR,
        'axes.labelcolor': CHART_TEXT_COLOR,
        'axes.edgecolor': CHART_TEXT_COLOR,
        'xtick.color': CHART_TEXT_COLOR,
        'ytick.color': CHART_TEXT_COLOR,
        'axes.titlecolor': CHART_TITLE_COLOR,
        'figure.facecolor': CHART_BG_COLOR,
        'axes.facecolor': CHART_BG_COLOR,
        'savefig.facecolor': CHART_BG_COLOR,
        'savefig.edgecolor': CHART_BG_COLOR,
    })

    # Plot based on type
    try:
        if chart_type == "bar":
            ax.bar(labels, values, color=CHART_PRIMARY_COLOR)
            ax.tick_params(axis='x', rotation=45) # Rotate labels if they overlap
        elif chart_type == "line":
            ax.plot(labels, values, marker='o', linestyle='-', color=CHART_PRIMARY_COLOR)
            ax.tick_params(axis='x', rotation=45)
        elif chart_type == "pie":
            # Pie charts might need different color handling
            colors = plt.cm.viridis([i/len(labels) for i in range(len(labels))]) # Example colormap
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, textprops={'color': CHART_TEXT_COLOR})
            ax.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.
        else:
            logger.error(f"Unsupported chart_type '{chart_type}' for section {section_index}.")
            plt.close(fig)
            return False

        ax.set_title(title, fontsize=CHART_FONT_SIZE_TITLE, color=CHART_TITLE_COLOR, weight='bold')
        # Add grid lines with appropriate color
        ax.grid(axis='y', color=CHART_TEXT_COLOR, linestyle='--', linewidth=0.5, alpha=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(CHART_TEXT_COLOR)
        ax.spines['bottom'].set_color(CHART_TEXT_COLOR)

        # Add axis labels if provided
        if x_label:
            ax.set_xlabel(x_label, fontsize=CHART_FONT_SIZE_LABEL, color=CHART_TEXT_COLOR)
        if y_label:
            ax.set_ylabel(y_label, fontsize=CHART_FONT_SIZE_LABEL, color=CHART_TEXT_COLOR)

        # Adjust tick label size and weight for visibility
        ax.tick_params(axis='both', which='major', labelsize=CHART_FONT_SIZE_TICKS, labelcolor=CHART_TEXT_COLOR)
        # Consider making tick labels bold if still not visible enough:
        # for label in ax.get_xticklabels() + ax.get_yticklabels():
        #     label.set_fontweight('bold')


        plt.tight_layout() # Adjust layout to prevent labels overlapping
        plt.savefig(output_filepath, dpi=CHART_DPI, transparent=False) # Ensure background is saved
        plt.close(fig) # Close the figure to free memory
        logger.info(f"Successfully rendered {chart_type} chart for section {section_index} to {output_filepath}")
        return True

    except Exception as e:
        logger.error(f"Failed to render Matplotlib chart for section {section_index}: {e}", exc_info=True)
        if 'fig' in locals() and plt:
             plt.close(fig) # Attempt to close figure on error
        return False


def render_visual_element(section_index: int, element_type: str, element_content: str, output_dir: str, temp_dir: str) -> Optional[str]:
    """
    Renders a visual element (Mermaid diagram or chart data) to a PNG image.

    Args:
        section_index: The index of the video section (for naming).
        element_type: The type of element ("diagram" or "chart_data").
        element_content: The string containing Mermaid code or JSON chart data.
        output_dir: The directory to save the generated PNG file.
        temp_dir: The directory to store temporary files.

    Returns:
        The path to the generated PNG file (str) or None if rendering failed.
    """
    if not element_content or not element_content.strip():
        logger.warning(f"No content provided for visual element in section {section_index}. Skipping rendering.")
        return None

    ensure_dir_exists(output_dir)
    ensure_dir_exists(temp_dir)

    # Define output path based on type for clarity, though both are PNG
    if element_type == "diagram":
        output_filename = f"section_{section_index}_diagram.png"
    elif element_type == "chart_data":
        output_filename = f"section_{section_index}_chart.png"
    else:
        logger.error(f"Unsupported visual element type '{element_type}' for section {section_index}.")
        return None

    output_filepath = os.path.join(output_dir, output_filename)

    success = False
    if element_type == "diagram":
        success = _render_mermaid_diagram(section_index, element_content, output_filepath, temp_dir)
    elif element_type == "chart_data":
        try:
            chart_data = json.loads(element_content)
            success = _render_matplotlib_chart(section_index, chart_data, output_filepath)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON content for chart_data in section {section_index}: {e}")
            success = False
        except Exception as e: # Catch potential errors during parsing or rendering setup
            logger.error(f"Error processing chart_data for section {section_index}: {e}", exc_info=True)
            success = False

    if success:
        return output_filepath
    else:
        # Attempt to remove potentially incomplete output file on failure
        if os.path.exists(output_filepath):
            try: os.remove(output_filepath)
            except OSError: pass
        return None


# Example usage
if __name__ == '__main__':
    print("Testing Visual Element Rendering...")
    test_output_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'diagrams') # Keep using diagrams dir for output
    test_temp_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'temp')
    print(f"Output directory: {test_output_dir}")
    print(f"Temp directory: {test_temp_dir}")

    # --- Test Mermaid ---
    print("\n--- Testing Mermaid ---")
    mermaid_code = """
graph TD;
    A[Start] --> B(Process 1);
    B --> C{Decision};
    C -- Yes --> D[End];
    C -- No --> B;
"""
    print(f"Mermaid CLI Path: {MERMAID_CLI_PATH}")
    diagram_path = render_visual_element(998, "diagram", mermaid_code, test_output_dir, test_temp_dir)
    if diagram_path:
        print(f"Successfully generated test diagram: {diagram_path}")
        try: os.remove(diagram_path); print(f"Cleaned up: {diagram_path}")
        except OSError as e: print(f"Warning: Failed to clean up {diagram_path}: {e}")
    else:
        print("Failed to generate test diagram.")
        print("Ensure '@mermaid-js/mermaid-cli' is installed and accessible.")

    # --- Test Matplotlib Chart ---
    print("\n--- Testing Matplotlib Chart ---")
    if MATPLOTLIB_AVAILABLE:
        chart_content_json = json.dumps({
            "chart_type": "bar",
            "labels": ["Apples", "Oranges", "Bananas"],
            "values": [5, 8, 3],
            "title": "Fruit Count"
        })
        chart_path = render_visual_element(999, "chart_data", chart_content_json, test_output_dir, test_temp_dir)
        if chart_path:
            print(f"Successfully generated test chart: {chart_path}")
            try: os.remove(chart_path); print(f"Cleaned up: {chart_path}")
            except OSError as e: print(f"Warning: Failed to clean up {chart_path}: {e}")
        else:
            print("Failed to generate test chart.")
    else:
        print("Skipping chart test: Matplotlib not found. Please install it (`pip install matplotlib`).")
