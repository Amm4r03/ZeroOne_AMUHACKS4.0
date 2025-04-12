from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import os
import json
from googleapiclient.discovery import build

load_dotenv()
router = APIRouter()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class InputData(BaseModel):
    syllabus: str
    subject: str
    class_level: str 
    exam: str
    difficulty: str
    timeline: str
    priorKnowledge: str

class Topic(BaseModel):
    name: str
    subtopics: List[str]
    completion_time: int  # Days to complete
    resources: List[str]
    youtube_link: str

def get_video_link(query, max_results=1):
    """Fetches YouTube video links for a given search query."""
    youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))

    request = youtube.search().list(
        q=query, 
        part="snippet",
        maxResults=max_results,
        type="video"
    )
    
    response = request.execute()
    
    video_links = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        video_links.append(f"https://www.youtube.com/watch?v={video_id}")
    
    return video_links if video_links else ["No video found"]


import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@router.post("/generate_topics/", response_model=List[Topic])
async def generate_topics(input_data: InputData):
    logger.debug(f"Received input data: {input_data}") # Log input data
    try:
        prompt = f"""
        Generate a detailed list of topics based on the following requirements, provided in JSON format.

        Syllabus: {input_data.syllabus}
        Subject: {input_data.subject}
        Class Level: {input_data.class_level}
        Target Exam: {input_data.exam}
        Difficulty Level: {input_data.difficulty}
        Desired Timeline: {input_data.timeline}
        Prior Knowledge: {input_data.priorKnowledge}

        Consider the difficulty, timeline, and prior knowledge when deciding the depth and breadth of topics and subtopics.
        Adjust the estimated completion_time for each topic based on the overall timeline and difficulty.

        Use this JSON schema for each topic in the list:
        Topic = {{'name': str, 'subtopics': list[str], 'completion_time': int, 'resources': list[str]}}
        Return: list[Topic]

        name: Name of the topic
        subtopics: List of subtopics for the topic
        completion_time: Number of days to complete the topic
        resources: List of resources for the topic.

        Note: For resources, mention recommended resources for each topic.
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        json_string = (response.text).strip("```json").strip("```").strip()

        try:
            topic_list = json.loads(json_string)
        except json.JSONDecodeError:
            topic_list = None
            raise HTTPException(status_code=500, detail="Invalid JSON response from Gemini API")

        for topic in topic_list:
            topic["youtube_link"] = (get_video_link(topic["name"]))[0]

        return topic_list

    except Exception as e:
        logger.exception("Error in generate_topics:") # Log the exception
        raise HTTPException(status_code=500, detail=str(e))
