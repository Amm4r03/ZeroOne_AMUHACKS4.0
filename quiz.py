from typing import List, Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from enum import Enum
from google import genai
import os
from dotenv import load_dotenv
import json

load_dotenv()
router = APIRouter()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class DifficultyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class QuestionType(str, Enum):
    multiple_choice = "multiple-choice"
    true_false = "true-false"
    mixed = "mixed" # Added mixed type

# response models for different question types
class MCQQuestion(BaseModel):
    question: str
    options: List[str] = Field(..., min_length=2)
    answer: str

class TrueFalseQuestion(BaseModel):
    question: str
    options: List[str] = ["True", "False"]
    answer: str # Will be "True" or "False"

QuizQuestionResponse = Union[MCQQuestion, TrueFalseQuestion]


class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    difficulty: DifficultyLevel
    questionCount: int = Field(default=5, gt=0)
    questionType: QuestionType


@router.post("/generate_quizzes/", response_model=List[QuizQuestionResponse])
async def generate_quizzes(quiz_request: QuizRequest):
    try:
        prompt = f"""
        Generate {quiz_request.questionCount} quiz questions about the topic: "{quiz_request.topic}".
        The difficulty level should be {quiz_request.difficulty.value}.
        The question type should be {quiz_request.questionType.value}.
        """

        if quiz_request.questionType == QuestionType.multiple_choice:
            prompt += """
        For multiple-choice questions, provide output as a JSON list using this schema for each question:
        {
            "question": "The question text (string)",
            "options": ["Option A (string)", "Option B (string)", "Option C (string)", "Option D (string)"],
            "answer": "The correct option text (string)"
        }
        Ensure exactly 4 options are provided for each multiple-choice question.
        """
        elif quiz_request.questionType == QuestionType.true_false:
            prompt += """
        For true/false questions, provide output as a JSON list using this schema for each question:
        {
            "question": "The statement (string)",
            "options": ["True", "False"],
            "answer": "True" or "False" (string)
        }
        """
        elif quiz_request.questionType == QuestionType.mixed:
             prompt += f"""
        Generate a mix of multiple-choice and true/false questions. Aim for roughly half of each type if possible, totaling {quiz_request.questionCount} questions.
        Provide output as a JSON list. Use the appropriate schema for each question type:
        - Multiple-Choice Schema: {{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "..." }} (Ensure 4 options)
        - True/False Schema: {{ "question": "...", "options": ["True", "False"], "answer": "True" or "False" }}
        """

        prompt += "\nReturn ONLY the JSON list, without any introductory text or markdown formatting."

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        # Clean the response text
        json_string = response.text
        if json_string.startswith("```json"):
            json_string = json_string[7:]
        if json_string.endswith("```"):
            json_string = json_string[:-3]
        json_string = json_string.strip()

        try:
            quiz_data = json.loads(json_string)
            if not isinstance(quiz_data, list):
                 raise ValueError("AI response is not a JSON list")

            # Validate each item in the list based on its structure
            validated_list = []
            for item in quiz_data:
                if "options" in item and len(item["options"]) > 2: # Heuristic for MCQ
                    validated_list.append(MCQQuestion(**item))
                elif "options" in item and item["options"] == ["True", "False"]: # Heuristic for T/F
                    validated_list.append(TrueFalseQuestion(**item))
                else:
                    try:
                        # Try MCQ first as it's more complex
                        validated_list.append(MCQQuestion(**item))
                    except Exception:
                        try:
                            validated_list.append(TrueFalseQuestion(**item))
                        except Exception:
                             raise ValueError(f"Unknown question structure in mixed response: {item}")

        except json.JSONDecodeError:
            print(f"Failed to decode JSON: {json_string}")
            raise HTTPException(status_code=500, detail="Invalid JSON response from AI model")
        except Exception as e:
             print(f"Error processing quiz list: {e}")
             raise HTTPException(status_code=500, detail=f"Error processing AI response: {e}")

        return validated_list
    except Exception as e:
        print(f"Error generating quizzes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quizzes: {str(e)}")
