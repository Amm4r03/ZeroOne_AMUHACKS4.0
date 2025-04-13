# -*- coding: utf-8 -*-
from manim import *

# Basic configuration matching the project
config.background_color = "#000000" # Black background
TEXT_COLOR = "#FFFFFF" # White text/equation

class TestLatexScene(Scene):
    def construct(self):
        # Test the specific problematic equation string (without extra escapes)
        equation_text = r"\frac{dT}{dt} = -k(T - T_{ambient})"

        try:
            # Create MathTex object, explicitly set color
            # MathTex usually adds the $ signs itself
            equation = MathTex(equation_text, font_size=72).set_color(TEXT_COLOR)

            # Display the equation
            self.play(Write(equation))
            self.wait(2) # Wait for 2 seconds

            print("\n--- TestLatexScene: Successfully created and added MathTex object. ---")

        except Exception as e:
            print(f"\n--- TestLatexScene: ERROR creating/adding MathTex object ---")
            print(f"Equation Text: {equation_text}")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Details: {e}")
            # Add a simple text message indicating failure
            error_message = Text("Failed to render LaTeX. Check console.", color=RED, font_size=36)
            self.play(Write(error_message))
            self.wait(2)

        print("--- TestLatexScene: construct() method finished. ---")
