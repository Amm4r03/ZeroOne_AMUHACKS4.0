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

class Input(BaseModel):
    topic: str

class Output(BaseModel):
    answer: str

@router.post("/about-topic/", response_model=List[Output])
async def generate_quizzes(inp: Input):
    try:
        prompt = f"""
        Generate 100-200 words summary about {inp.topic}.
        Provide output in JSON format using the schema:
        
        {{"answer": "your_summary_here"}}
        
        DO NOT INCLUDE ANYTHING ELSE IN YOUR OUTPUT.
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        json_string = response.text.strip("```json").strip("```").strip()

        try:
            data = json.loads(json_string)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from Gemini API")

        # Validate response structure
        if "answer" not in data or not isinstance(data["answer"], str):
            raise HTTPException(status_code=500, detail="Invalid response structure from Gemini API")

        return [Output(**data)]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))