import unittest
import os
import subprocess
from unittest.mock import patch, MagicMock

import logging
from unittest.mock import patch, MagicMock, call

from edu_video_generator.src.diagram_renderer import render_visual_element, _render_mermaid_diagram
from edu_video_generator.src.utils import logger as actual_logger

# Patch the logger where it's USED in the diagram_renderer module
@patch('edu_video_generator.src.diagram_renderer.logger')
# Patch the check for mmdc existence
@patch('edu_video_generator.src.diagram_renderer.check_mmdc_exists')
# Patch the actual subprocess call
@patch('subprocess.run')
class TestDiagramRenderer(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        self.test_dir = "edu_video_generator/tests/temp_test_assets"
        self.output_dir = os.path.join(self.test_dir, "diagrams")
        self.temp_dir = os.path.join(self.test_dir, "temp")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        self.section_index = 1
        self.mermaid_code = "graph TD;\nA-->B;"
        self.expected_output_filename = f"section_{self.section_index}_diagram.png"
        self.expected_output_path = os.path.join(self.output_dir, self.expected_output_filename)
        # Store the path to the potential output file for cleanup
        self.file_to_cleanup = self.expected_output_path

    def tearDown(self):
        """Clean up created files and directories after each test."""
        # Clean up the specific output file if it exists
        if self.file_to_cleanup and os.path.exists(self.file_to_cleanup):
            os.remove(self.file_to_cleanup)
            self.file_to_cleanup = None # Reset for next test

        # Clean up temporary files created by the code (if any remain due to errors)
        # Note: The code uses tempfile.NamedTemporaryFile with delete=False,
        # and cleans up in a finally block, so this might not be strictly necessary
        # unless the cleanup fails.
        if os.path.exists(self.temp_dir):
            for f in os.listdir(self.temp_dir):
                try:
                    os.remove(os.path.join(self.temp_dir, f))
                except OSError:
                    pass # Ignore if file is already gone
            os.rmdir(self.temp_dir)

        if os.path.exists(self.output_dir):
            os.rmdir(self.output_dir)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_render_visual_element_diagram_success(self, mock_subprocess_run, mock_check_mmdc, mock_logger):
        """Test successful rendering of a Mermaid diagram."""
        # Arrange: Mock mmdc exists and subprocess success
        mock_check_mmdc.return_value = True
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        # Act: Call the main function for diagrams
        result_path = render_visual_element(
            section_index=self.section_index,
            element_type="diagram",
            element_content=self.mermaid_code,
            output_dir=self.output_dir,
            temp_dir=self.temp_dir
        )

        # Assert
        mock_check_mmdc.assert_called_once() # Ensure mmdc check happens
        self.assertTrue(mock_subprocess_run.called) # Ensure subprocess was called

        # Check the arguments passed to subprocess.run
        args, kwargs = mock_subprocess_run.call_args
        command_list = args[0]
        self.assertIn("mmdc", command_list[0]) # Check command executable (might include full path)
        self.assertIn("-i", command_list) # Check input flag
        # The input file is temporary, so checking its exact name is fragile.
        # Check other flags instead.
        self.assertIn("-o", command_list)
        self.assertIn(self.expected_output_path, command_list) # Check output path
        self.assertIn("-w", command_list)
        self.assertIn("1920", command_list) # Check default width
        self.assertIn("-H", command_list)
        self.assertIn("1080", command_list) # Check default height
        self.assertIn("-t", command_list)
        self.assertIn("neutral", command_list) # Check default theme
        self.assertIn("-b", command_list)
        self.assertIn("transparent", command_list) # Check default background

        # Check return value
        self.assertEqual(result_path, self.expected_output_path)

        # Check logs (optional, but good practice)
        mock_logger.info.assert_any_call(f"Executing Mermaid CLI command: {' '.join(command_list)}")
        mock_logger.info.assert_any_call(f"Successfully rendered Mermaid diagram for section {self.section_index} to {self.expected_output_path}")

    def test_render_visual_element_diagram_cli_failure(self, mock_subprocess_run, mock_check_mmdc, mock_logger):
        """Test handling of Mermaid CLI failure (e.g., parse error)."""
        # Arrange: Mock mmdc exists, but subprocess fails
        mock_check_mmdc.return_value = True
        error_message = "Error: Parse error on line 1: ..." # Simplified error
        mock_subprocess_run.return_value = MagicMock(returncode=1, stdout="Generating single mermaid chart", stderr=error_message)

        # Act
        result_path = render_visual_element(
            section_index=self.section_index,
            element_type="diagram",
            element_content="graph LR; A-- Invalid -> B;", # Example invalid syntax
            output_dir=self.output_dir,
            temp_dir=self.temp_dir
        )

        # Assert
        mock_check_mmdc.assert_called_once()
        self.assertTrue(mock_subprocess_run.called)
        self.assertIsNone(result_path) # Function should return None on failure

        # Check error logs
        mock_logger.error.assert_any_call(f"Mermaid CLI failed for section {self.section_index} (Return Code: 1)")
        mock_logger.error.assert_any_call(f"Stderr: {error_message}")
        # Ensure the success log was NOT called
        success_log = f"Successfully rendered Mermaid diagram for section {self.section_index} to {self.expected_output_path}"
        self.assertNotIn(call(success_log), mock_logger.info.call_args_list)

    def test_render_visual_element_diagram_mmdc_not_found(self, mock_subprocess_run, mock_check_mmdc, mock_logger):
        """Test behavior when Mermaid CLI executable is not found."""
        # Arrange: Mock mmdc check returns False
        mock_check_mmdc.return_value = False

        # Act
        result_path = render_visual_element(
            section_index=self.section_index,
            element_type="diagram",
            element_content=self.mermaid_code,
            output_dir=self.output_dir,
            temp_dir=self.temp_dir
        )

        # Assert
        mock_check_mmdc.assert_called_once()
        mock_subprocess_run.assert_not_called() # Subprocess should not run if mmdc not found
        self.assertIsNone(result_path) # Should return None

        # Note: We don't assert the logger call from *within* the mocked check_mmdc_exists function,
        # as the mock replaces the function entirely. The important part is that
        # render_visual_element handles the False return value correctly.

    def test_render_visual_element_empty_content(self, mock_subprocess_run, mock_check_mmdc, mock_logger):
        """Test behavior with empty diagram content."""
        # Arrange (mmdc check doesn't matter here as it short-circuits)
        empty_mermaid_code = "  \n \t " # Whitespace only

        # Act
        result_path = render_visual_element(
            section_index=self.section_index,
            element_type="diagram",
            element_content=empty_mermaid_code,
            output_dir=self.output_dir,
            temp_dir=self.temp_dir
        )

        # Assert
        mock_check_mmdc.assert_not_called() # Should not check for mmdc if content is empty
        mock_subprocess_run.assert_not_called()
        self.assertIsNone(result_path)

        # Check warning log
        mock_logger.warning.assert_called_once_with(f"No content provided for visual element in section {self.section_index}. Skipping rendering.")


    # TODO: Add tests for chart rendering if needed
    # @patch('edu_video_generator.src.diagram_renderer._render_matplotlib_chart')
    # def test_render_visual_element_chart_success(self, mock_render_chart, mock_subprocess_run, mock_check_mmdc, mock_logger):
    #     ...

    # Add more tests:
    # - Test different mermaid syntaxes if variations are expected (less critical if mocking subprocess)
    # - Test for non-existent output/temp directories (if not handled by makedirs)
    # - Test different mermaid syntaxes if variations are expected

if __name__ == '__main__':
    unittest.main()
