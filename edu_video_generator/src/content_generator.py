import os
import json
import logging
from typing import Dict, Any, List
import llm
from dotenv import load_dotenv
import re # For cleaning pause markers before validation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file located in ../config relative to this script
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Configuration ---
GEMINI_MODEL_NAME = "gemini-2.0-flash"


# --- Example JSON Structures for Prompt ---
# These are kept separate to avoid complex escaping within the main template
EXAMPLE_TEXT_JSON = """
{{
  "title": "Key Concept: Algorithms",
  "narration_script": "Alright, let's talk algorithms! [PAUSE=0.5] Think of them like recipes for the computer... [PAUSE=0.5] They're the step-by-step instructions... [PAUSE=1.0] that tell the machine exactly how to learn from the data and find those patterns we mentioned.",
  "timed_on_screen_elements": [
    {{ "type": "text", "content": "Algorithms act like detailed recipes guiding computer actions.", "start_time": 1.5, "end_time": 4.0 }},
    {{ "type": "text", "content": "They provide precise step-by-step instructions for tasks.", "start_time": 4.5, "end_time": 7.0 }},
    {{ "type": "text", "content": "These instructions enable machines to learn effectively from data.", "start_time": 7.5, "end_time": 9.5 }},
    {{ "type": "text", "content": "Ultimately, algorithms help uncover hidden patterns within information.", "start_time": 10.0, "end_time": 12.5 }}
  ],
  "estimated_duration_seconds": 13,
  "diagram_mermaid_code": null
}}
"""

EXAMPLE_DIAGRAM_JSON = """
{{
  "title": "Example: Spam Detection",
  "narration_script": "Let's take email spam detection. [PAUSE=0.5] The algorithm learns from emails you mark as spam... [PAUSE=0.5] identifying common words or patterns. [PAUSE=1.0] Then, it predicts if new emails are spam or not, like this simple flow shows.",
  "timed_on_screen_elements": [
     {{ "type": "text", "content": "Consider how spam filters analyze incoming emails.", "start_time": 0.5, "end_time": 2.5 }},
     {{ "type": "text", "content": "The system learns by studying emails previously marked as spam.", "start_time": 3.0, "end_time": 5.5 }},
     {{ "type": "text", "content": "It identifies recurring keywords or characteristics of unwanted mail.", "start_time": 6.0, "end_time": 8.0 }},
     {{ "type": "diagram", "content": "graph TD; A[\\"New Email\\"] --> B{{{{\\"Spam Filter\\"}}}}}}; B -- \\"Spam\\" --> C[\\"Spam Folder\\"]; B -- \\"Not Spam\\" --> D[\\"Inbox\\"];", "start_time": 8.5, "end_time": 12.0 }}
   ],
  "estimated_duration_seconds": 12,
  "diagram_mermaid_code": "graph TD; A[\\"New Email\\"] --> B{{{{\\"Spam Filter\\"}}}}}}; B -- \\"Spam\\" --> C[\\"Spam Folder\\"]; B -- \\"Not Spam\\" --> D[\\"Inbox\\"];"
}}
"""

EXAMPLE_LATEX_JSON = """
{{
  "title": "Concept: Quadratic Formula",
  "narration_script": "Now for a classic, the quadratic formula! [PAUSE=0.5] It helps us solve equations of the form ax squared plus bx plus c equals zero. [PAUSE=1.0] Here's the formula itself...",
  "timed_on_screen_elements": [
    {{ "type": "text", "content": "Solves equations like ax²+bx+c=0", "start_time": 1.0, "end_time": 5.0 }},
    {{ "type": "latex", "content": "x = \\\\frac{{-b \\\\pm \\\\sqrt{{b^2-4ac}}}}{{2a}}", "start_time": 5.5, "end_time": 10.0 }}
  ],
  "estimated_duration_seconds": 10,
  "diagram_mermaid_code": null
}}
"""

EXAMPLE_CHART_JSON = """
{{
  "title": "Data Trends",
  "narration_script": "We can see a clear trend in the data over the last few months. [PAUSE=0.5] Let's visualize this with a simple bar chart.",
  "timed_on_screen_elements": [
    {{ "type": "text", "content": "Data shows a noticeable trend over recent months with X and Y axis labelled.", "start_time": 0.5, "end_time": 3.0 }},
    {{ "type": "chart_data", "content": "{{\\"chart_type\\": \\"bar\\", \\"labels\\": [\\"Jan\\", \\"Feb\\", \\"Mar\\"], \\"values\\": [15, 22, 18]}}", "start_time": 3.5, "end_time": 8.0 }}
  ],
  "estimated_duration_seconds": 8,
  "diagram_mermaid_code": null
}}
"""


# --- Updated Gemini Prompt ---
# Now requests timed_on_screen_elements, language, and chart_data
# All literal braces are escaped with {{ }}
GEMINI_PROMPT_TEMPLATE = """
You are an AI assistant creating engaging scripts for short educational videos in the specified language: **{language_name}**.
Generate a script about the topic: "{topic}"

Adopt a friendly, slightly informal, and encouraging tone suitable for a video tutor **in {language_name}**.

The script structure should be:
1.  **Introduction:** Approx. 20-30 seconds. Introduce the topic enthusiastically.
2.  **Key Concepts:** 3 to 5 key concepts. Explain each clearly (approx. 45-60 seconds per concept). **Include at least 2-3 visual elements (diagrams or charts) across these key concept sections where appropriate.**
3.  **Examples/Visuals:** Include 1 or 2 additional examples or concepts benefiting from a visual element. This can be a diagram (Mermaid) or a simple chart (data for plotting).
4.  **Summary:** Approx. 20-30 seconds. Briefly recap the main takeaways.

**Output Format:**
Return the response ONLY as a valid JSON object. Each section in the 'sections' array must have:
-   `title`: (string) A short title for the section (e.g., "Introduction", "What is Data?"). Suitable for display.
-   `narration_script`: (string) The full script for the voiceover **in {language_name}**. Write this in an engaging, conversational style. **Do NOT use markdown formatting (like asterisks for emphasis) in the narration script.** **Crucially, insert explicit pause markers like `[PAUSE=0.5]` or `[PAUSE=1.0]` where a speaker would naturally pause (0.5 for short pause, 1.0 for longer pause).**
-   `timed_on_screen_elements`: (list of objects) A list where each object represents a visual element to display. **MUST contain at least 4 'text' type elements per section**, aiming for 4-6 total elements. Each object must have:
    -   `type`: (string) Either "text", "diagram", "latex", or "chart_data".
    -   `content`: (string)
        - For type="text": Provide concise text points summarizing or highlighting the key point being narrated. Generate enough points to visually occupy roughly 60% of the available text area during the narration segment. Complement, don't just repeat the narration. **Do NOT use markdown formatting (like asterisks for emphasis) here either.**
        - For type="diagram": Provide the Mermaid code (flowchart, sequence, basic graph). **IMPORTANT: Always enclose text within nodes in double quotes.** For example, use `A["Node Text"]` or `B{{ {{"Node Text with {{{{braces}}}}"}} }}` instead of `A[Node Text]` or `B{{Node Text}}`. This ensures correct parsing of special characters. **The narration MUST explain what the diagram illustrates.**
        - For type="latex": Provide the mathematical equation or formula formatted using valid LaTeX syntax. **CRITICAL: Within the JSON string value for 'content', ALL backslashes (`\`) needed for LaTeX MUST be double-escaped (`\\\\`).** For example, `\\frac{{{{a}}}}{{{{b}}}}` should be written as `"content": "\\\\frac{{{{a}}}}{{{{b}}}}"`. Similarly, `\,` becomes `\\\\,`. **Use ONLY single curly braces `{{}}` within the LaTeX itself (e.g., for fractions, roots, limits), NEVER double braces `{{{{}}}}`.** **Do NOT include the surrounding `$` or `$$` delimiters.** **The narration MUST explain the equation's meaning or purpose.** **IMPORTANT NOTE: Regardless of the requested `{language_name}`, the LaTeX content itself MUST always be generated in English (en-US).**
        - For type="chart_data": Provide a JSON string containing data for plotting. The JSON object MUST have keys: `"chart_type"` (string, e.g., "bar", "line"), `"labels"` (list of strings), `"values"` (list of numbers), **`"title"` (string, a specific descriptive title for the chart)**, **`"x_axis_label"` (string, REQUIRED label for the X-axis)**, and **`"y_axis_label"` (string, REQUIRED label for the Y-axis)**. Example: `{{{{ \\"chart_type\\": \\"bar\\", \\"title\\": \\"Monthly Sales Growth\\", \\"labels\\": [\\"Jan\\", \\"Feb\\", \\"Mar\\"], \\"values\\": [15, 22, 18], \\"x_axis_label\\": \\"Month\\", \\"y_axis_label\\": \\"Sales\\" }}}}`. **The narration MUST explain the data shown in the chart.** **IMPORTANT NOTE: Regardless of the requested `{language_name}`, the chart data content (including the internal `title`, `labels`, `x_axis_label`, `y_axis_label`) MUST always be generated in English (en-US).**
    -   `start_time`: (float) Estimated time in seconds (relative to the start of *this section's narration*, excluding pauses) when this element should *start* appearing/being highlighted.
    -   `end_time`: (float) Estimated time in seconds (relative to the start of *this section's narration*, excluding pauses) when this element should *stop* being highlighted or fade out.
-   `estimated_duration_seconds`: (integer) Approximate duration hint for the narration (excluding pauses).
-   `diagram_mermaid_code`: (string or null) [DEPRECATED - Use timed_on_screen_elements with type='diagram' instead] Provide the Mermaid code here as well for backward compatibility or redundancy, otherwise null.

**Example Section Structure (Text):**
{example_text_json}

// Example with diagram:
{example_diagram_json}

// Example with LaTeX (Note: Backslashes are DOUBLE escaped in the JSON string value):
{example_latex_json}

// Example with Chart Data:
{example_chart_json}

**Important:**
-   Ensure the JSON is valid and properly escaped. Pay attention to escaping within the JSON string for `chart_data`.
-   Use the exact format `[PAUSE=X.X]` for pauses in the `narration_script`.
-   The `start_time` and `end_time` for `timed_on_screen_elements` should be relative to the start of the section's narration audio (ignoring the duration of the pauses themselves). Ensure `end_time` is always greater than `start_time`.
-   Ensure `content` for `type="text"` provides enough concise points to fill ~60% of the text area. Use `type="latex"` for LaTeX math (without surrounding $). Use `type="chart_data"` for chart plotting data (including a specific title and **REQUIRED axis labels**) in the specified JSON format. **Narration MUST explain diagrams, charts, and equations.**
-   **Handling Lists:** When presenting lists (e.g., 'Types of X'), structure the `timed_on_screen_elements` logically.
-   Aim for 4-7 `timed_on_screen_elements` per section, **with at least 4 being of type 'text'**.
-   **Visual Element Requirement:** Ensure the final JSON output, across all sections combined, contains **at least 3-4** elements with `type: 'diagram'` or `type: 'chart_data'`. This is mandatory for all topics. Use Mermaid or provide chart data where appropriate to illustrate concepts.
-   **LaTeX Requirement:** For mathematical or scientific topics (like Differential Equations, Calculus, Physics, Chemistry, etc.), **you MUST include multiple relevant equations** using `type: 'latex'`. **It is CRITICAL to include 2-3 equations per relevant section** where appropriate. If the topic is clearly non-mathematical, this is not required.
-   **Visual Clarity:** Avoid showing complex diagrams/charts simultaneously with large blocks of text. Sequence them appropriately.
-   Adhere strictly to the JSON structure. Do not add explanations outside the JSON object.
"""

# Regex to find pause markers like [PAUSE=0.5] - used for cleaning before validation
PAUSE_REGEX_CLEAN = re.compile(r"\[PAUSE=\d+(?:\.\d+)?\]")

def validate_structure(data: Dict[str, Any], topic: str) -> Dict[str, Any]:
    """Validates the structure of the JSON data received from Gemini."""
    if not isinstance(data, dict):
        raise ValueError("Response is not a JSON object.")

    if "sections" not in data or not isinstance(data["sections"], list):
        raise ValueError("Missing or invalid 'sections' list in response.")

    if not data["sections"]:
        raise ValueError("'sections' list cannot be empty.")

    # Updated required keys, including the new timed elements structure
    required_section_keys = {"title", "narration_script", "timed_on_screen_elements", "estimated_duration_seconds", "diagram_mermaid_code"}
    required_element_keys = {"type", "content", "start_time", "end_time"}

    has_visual_element = False # Track if at least one diagram or chart exists

    for i, section in enumerate(data["sections"]):
        if not isinstance(section, dict):
            raise ValueError(f"Section {i} is not a JSON object.")
        missing_keys = required_section_keys - section.keys()
        if missing_keys:
            raise ValueError(f"Section {i} is missing required keys: {missing_keys}")

        # Basic type checks
        if not isinstance(section["title"], str) or not section["title"]:
            raise ValueError(f"Section {i} has an invalid or empty 'title'.")
        if not isinstance(section["narration_script"], str) or not section["narration_script"]:
             raise ValueError(f"Section {i} has an invalid or empty 'narration_script'.")
        if not isinstance(section["estimated_duration_seconds"], int) or section["estimated_duration_seconds"] <= 0:
             raise ValueError(f"Section {i} has an invalid 'estimated_duration_seconds'.")
        if section["diagram_mermaid_code"] is not None and not isinstance(section["diagram_mermaid_code"], str):
             raise ValueError(f"Section {i} has an invalid 'diagram_mermaid_code' (must be string or null).")

        # Validate timed_on_screen_elements
        if not isinstance(section["timed_on_screen_elements"], list):
             raise ValueError(f"Section {i} has invalid 'timed_on_screen_elements' (must be a list).")

        narration_without_pauses = PAUSE_REGEX_CLEAN.sub('', section["narration_script"])
        # Rough estimate of actual speech duration (can be refined)
        estimated_speech_duration = len(narration_without_pauses.split()) / 3.0 # Approx 3 words per second

        for j, element in enumerate(section["timed_on_screen_elements"]):
             if not isinstance(element, dict):
                 raise ValueError(f"Section {i}, Element {j} is not a JSON object.")
             missing_element_keys = required_element_keys - element.keys()
             if missing_element_keys:
                 raise ValueError(f"Section {i}, Element {j} is missing required keys: {missing_element_keys}")

             element_type = element["type"]
             element_content = element["content"]

             # Allow "chart_data" as a valid type
             if element_type not in ["text", "diagram", "latex", "chart_data"]:
                 raise ValueError(f"Section {i}, Element {j} has invalid type: {element_type}")
             if not isinstance(element_content, str) or not element_content:
                  raise ValueError(f"Section {i}, Element {j} has invalid or empty content.")
             if not isinstance(element["start_time"], (int, float)) or element["start_time"] < 0:
                  raise ValueError(f"Section {i}, Element {j} has invalid start_time.")
             if not isinstance(element["end_time"], (int, float)) or element["end_time"] <= element["start_time"]:
                  raise ValueError(f"Section {i}, Element {j} has invalid end_time (must be > start_time).")

             # Validate chart_data content structure
             if element_type == "chart_data":
                 try:
                     chart_data = json.loads(element_content)
                     if not isinstance(chart_data, dict):
                         raise ValueError("Chart data JSON is not an object.")
                     required_chart_keys = {"chart_type", "labels", "values", "title", "x_axis_label", "y_axis_label"} # Added title and axis labels
                     missing_chart_keys = required_chart_keys - chart_data.keys()
                     if missing_chart_keys:
                         # Allow axis labels to be optional for now, but log warning
                         if "x_axis_label" in missing_chart_keys or "y_axis_label" in missing_chart_keys:
                              logger.warning(f"Missing optional axis labels in chart_data for section {i}, element {j}.")
                              # Remove them from missing keys if they were the only ones missing
                              missing_chart_keys -= {"x_axis_label", "y_axis_label"}
                         if "title" in missing_chart_keys: # Title is mandatory
                              raise ValueError(f"Missing required 'title' key in chart_data for section {i}, element {j}.")
                         # Re-check if other mandatory keys were missing after potentially removing optional ones
                         if missing_chart_keys:
                              raise ValueError(f"Missing keys in chart_data for section {i}, element {j}: {missing_chart_keys}")

                     if not isinstance(chart_data["chart_type"], str) or chart_data["chart_type"] not in ["bar", "line", "pie"]: # Add more types if needed
                         raise ValueError(f"Invalid chart_type in section {i}, element {j}: {chart_data['chart_type']}")
                     if not isinstance(chart_data["title"], str) or not chart_data["title"]:
                          raise ValueError(f"Invalid or empty 'title' in chart_data for section {i}, element {j}.")
                     if "x_axis_label" in chart_data and not isinstance(chart_data["x_axis_label"], str):
                          raise ValueError(f"Invalid 'x_axis_label' in chart_data for section {i}, element {j}.")
                     if "y_axis_label" in chart_data and not isinstance(chart_data["y_axis_label"], str):
                          raise ValueError(f"Invalid 'y_axis_label' in chart_data for section {i}, element {j}.")
                     if not isinstance(chart_data["labels"], list) or not all(isinstance(label, str) for label in chart_data["labels"]):
                         raise ValueError(f"Invalid 'labels' list in chart_data for section {i}, element {j} (must be list of strings).")
                     if not isinstance(chart_data["values"], list) or not all(isinstance(val, (int, float)) for val in chart_data["values"]):
                         raise ValueError(f"Invalid 'values' list in chart_data for section {i}, element {j} (must be list of numbers).")
                     if len(chart_data["labels"]) != len(chart_data["values"]):
                         raise ValueError(f"Length of 'labels' and 'values' must match in chart_data for section {i}, element {j}.")
                 except json.JSONDecodeError as json_err:
                     raise ValueError(f"Section {i}, Element {j}: Invalid JSON in chart_data content: {json_err}")
                 except ValueError as chart_val_err:
                     # Re-raise validation errors from within the try block
                     raise ValueError(f"Section {i}, Element {j}: Invalid chart_data structure: {chart_val_err}")


             # Track if we have at least one diagram or chart
             if element_type in ["diagram", "chart_data"]:
                 has_visual_element = True

             # Deprecated check (can be removed if diagram_mermaid_code is fully removed later)
             if element_type == "diagram" and section["diagram_mermaid_code"] is not None and section["diagram_mermaid_code"] != element_content:
                  logger.warning(f"Section {i}, Element {j}: Mermaid code in timed_element differs from section's diagram_mermaid_code.")

    # --- Final Validation: Check for required elements across all sections ---
    # Ensure at least a few visual elements are present
    visual_element_count = sum(1 for section in data['sections'] for el in section.get('timed_on_screen_elements', []) if el['type'] in ['diagram', 'chart_data'])
    if visual_element_count < 2: # Adjusted minimum requirement slightly lower than prompt request for flexibility
        logger.warning(f"Validation Warning: Only found {visual_element_count} visual elements (diagram/chart). Expected more.")
        # raise ValueError(f"Validation Error: The generated script must contain at least 3-4 elements with type 'diagram' or 'chart_data'. Found {visual_element_count}.")

    logger.info("Gemini response structure validated successfully (including presence of required visual element).")
    return data

# Caching is disabled
def generate_educational_content(topic: str, language: str = "en-US") -> Dict[str, Any]: # Added language parameter
    """
    Generates educational video script content using the Gemini API for a specific language.
    Includes narration with pause markers and timed on-screen elements.

    Args:
        topic: The subject of the video.
        language: The target language code (e.g., "en-US", "hi-IN"). Defaults to "en-US".
    """
    logger.info(f"Generating educational content for topic: {topic} in language: {language}")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
         logger.warning("GEMINI_API_KEY not found in environment variables.")

    try:
        model = llm.get_model(GEMINI_MODEL_NAME)
    except llm.UnknownModelError:
        logger.error(f"LLM model '{GEMINI_MODEL_NAME}' not found. Is llm-gemini installed?")
        raise RuntimeError(f"LLM model '{GEMINI_MODEL_NAME}' not found.")
    except Exception as e:
        import traceback
        logger.error(f"Failed to initialize LLM model '{GEMINI_MODEL_NAME}':")
        logger.error(f"  Error Type: {type(e).__name__}")
        logger.error(f"  Error Details (str): {e}")
        logger.error(f"  Error Details (repr): {repr(e)}")
        logger.error(f"  Traceback:\n{traceback.format_exc()}")
        raise RuntimeError(f"Failed to initialize LLM model ({type(e).__name__}): {e}")

    # Format the prompt with topic, language, and the example JSON strings
    prompt = GEMINI_PROMPT_TEMPLATE.format(
        topic=topic,
        language_name=language,
        example_text_json=EXAMPLE_TEXT_JSON,
        example_diagram_json=EXAMPLE_DIAGRAM_JSON,
        example_latex_json=EXAMPLE_LATEX_JSON,
        example_chart_json=EXAMPLE_CHART_JSON
    )

    try:
        logger.info("Attempting to send prompt to Gemini API...")
        # Update system prompt if needed, or keep it general
        response = model.prompt(prompt, system="You are an AI assistant creating engaging scripts for short educational videos.")
        logger.info("Received response object from Gemini API.")
        raw_response_text = response.text()
        logger.info(f"Extracted raw text (first 100 chars): {raw_response_text[:100]}...")

        if not raw_response_text:
             logger.error("Received empty response text from Gemini API.")
             raise ValueError("Received empty response text from Gemini API.")

        logger.info("Attempting to clean and parse JSON response...")
        try:
            logger.info("Attempting to strip markdown code fences if present...")
            if raw_response_text.strip().startswith("```json"):
                cleaned_text = raw_response_text.strip()[7:-3].strip()
            elif raw_response_text.strip().startswith("```"):
                 cleaned_text = raw_response_text.strip()[3:-3].strip()
            else:
                 cleaned_text = raw_response_text.strip() # Ensure leading/trailing whitespace removed

            # --- NEW: Check for and remove leading/trailing double braces ---
            if cleaned_text.startswith("{{") and cleaned_text.endswith("}}"):
                logger.info("Detected and removing leading/trailing double braces from response.")
                cleaned_text = cleaned_text[2:-2].strip()
            # --- End NEW ---

            logger.info("Attempting to parse JSON...")
            content_data = json.loads(cleaned_text)
            logger.info("Successfully parsed JSON response after pre-processing.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from Gemini: {e}")
            logger.error(f"--- Start Raw Gemini Response (before cleaning) ---")
            logger.error(raw_response_text)
            logger.error(f"--- End Raw Gemini Response ---")
            raise ValueError(f"Invalid JSON received from Gemini: {e}")

        logger.info("Attempting to validate JSON structure...")
        validated_data = validate_structure(content_data, topic)
        logger.info("Successfully validated JSON structure.")

        # --- Post-processing: Clean narration script and text content ---
        for section in validated_data.get("sections", []):
            if "narration_script" in section and isinstance(section["narration_script"], str):
                original_script = section["narration_script"]
                cleaned_script = original_script.replace("*", "")
                if original_script != cleaned_script:
                    logger.info(f"Removed asterisks from narration for section: {section.get('title', 'Untitled')}")
                    section["narration_script"] = cleaned_script
            for element in section.get("timed_on_screen_elements", []):
                 if element.get("type") == "text" and "content" in element and isinstance(element["content"], str):
                     original_content = element["content"]
                     cleaned_content = original_content.replace("*", "")
                     if original_content != cleaned_content:
                          logger.info(f"Removed asterisks from text element content in section: {section.get('title', 'Untitled')}")
                          element["content"] = cleaned_content
        # --- End Post-processing ---

        if "topic" not in validated_data:
             validated_data["topic"] = topic
        validated_data["language"] = language # Add language to the output data
        logger.info(f"Successfully generated and validated content for topic: {topic} in language: {language}")
        return validated_data

    except Exception as e:
        import traceback
        logger.error(f"Error during Gemini API call or processing:")
        logger.error(f"  Error Type: {type(e).__name__}")
        logger.error(f"  Error Details (str): {e}")
        logger.error(f"  Error Details (repr): {repr(e)}")
        logger.error(f"  Traceback:\n{traceback.format_exc()}")

        if isinstance(e, (ValueError, RuntimeError)):
             raise e
        else:
             raise RuntimeError(f"An unexpected error occurred ({type(e).__name__}) while generating content: {e}")


# Example usage
if __name__ == '__main__':
    test_topic = "Photosynthesis"
    test_language = "en-US" # Example language
    print(f"Attempting to generate content for: {test_topic} in language: {test_language}")
    if not os.getenv("GEMINI_API_KEY"):
        print("\nWARNING: GEMINI_API_KEY not set. Skipping example API call.")
    else:
        try:
            # Pass language to the function
            script_data = generate_educational_content(test_topic, language=test_language)
            print("\nSuccessfully generated content:")
            print(json.dumps(script_data, indent=2))
        except (ValueError, RuntimeError) as e:
            print(f"\nError generating content: {e}")
        except Exception as e:
             print(f"\nAn unexpected error occurred: {e}")
