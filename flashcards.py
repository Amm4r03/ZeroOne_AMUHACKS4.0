from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai
import os
from dotenv import load_dotenv
import json

load_dotenv()

router = APIRouter()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class Flashcard(BaseModel):
    question: str
    hint: str
    answer: str

class FlashcardRequest(BaseModel):
    topic: str
    difficulty: str
    num_flashcards: int

class FlashcardResponse(BaseModel):
    flashcards: List[Flashcard]
    error: str = None
    message: str = None

@router.post("/generate_flashcards", response_model=FlashcardResponse)
async def generate_flashcards(request: FlashcardRequest):
    try:
        # generating the flashcards using the API
        prompt = f"""
            Generate {request.num_flashcards} flashcards on the
            topic '{request.topic}' with difficulty
            '{request.difficulty}'.
            Make sure the flashcards follow the following guidelines
            to ensure maximum retention for the user :
                1. use active recall
                2. phrase questions so that they make the user think, and NOT regurgitate
                3. Allow cards that can be implemented with spaced repetition
                4. keep the cards simple : one idea per card
                5. avoid paragraphs : aim for short and clear prompts that get the mind running
                6. add question like 'why', 'how', or 'when' if applicable to deepen understanding
                7. Use Cloze Deletion : fill in the blanks style flashcards to help with definitions, formulae, and coding syntax     
                8. Interleave between subtopics : mix up different topics to improve retention

            Provide output in JSON format with the following schema:
            {{
                "flashcards": [
                    {{
                        "question": "<question>",
                        "hint": "<hint>",
                        "answer": "<answer>"
                    }}
                ]
            }}
            Ensure that the questions are clear and concise.
            """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        if not response.text:
            raise HTTPException(status_code=500, detail="Empty response from Gemini API")

        # parse the response to extract flashcards
        flashcards_data = (response.text).strip("```json").strip("```")

        try:
            flashcards_data = json.loads(flashcards_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to decode the JSON response")

        # ensure and enforce proper structure for flashcards
        if "flashcards" not in flashcards_data:
            raise HTTPException(status_code=500, detail="Invalid response structure, 'flashcards' key missing")

        flashcards = [
            Flashcard(question=fc['question'], hint=fc['hint'], answer=fc['answer'])
            for fc in flashcards_data['flashcards']
        ]

        return FlashcardResponse(flashcards=flashcards, message="Flashcards generated successfully.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))