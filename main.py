from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# Import routers
from generate_topics import router as topics_router
from quiz import router as quizzes_router
from about import router as about_router
from flashcards import router as flashcards_router

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics_router)
app.include_router(quizzes_router)
app.include_router(about_router)
app.include_router(flashcards_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7070)
