from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. MOCK DATABASE ---
question_bank = [
    {"id": 1, "topic": "Arrays", "difficulty": "easy", "text": "What is the time complexity of accessing an element in an array?", "correct": "O(1)"},
    {"id": 2, "topic": "Arrays", "difficulty": "medium", "text": "Find the missing number in an array of 1 to N.", "correct": "n*(n+1)/2 - sum"},
    {"id": 3, "topic": "Arrays", "difficulty": "hard", "text": "Explain the logic for trapping rain water problem.", "correct": "Two pointer"},
    {"id": 4, "topic": "DP", "difficulty": "easy", "text": "What is the base case for Fibonacci DP?", "correct": "n<=1"},
]

# Global state (In a real app, this would be in a DB keyed by user_id)
user_state = {
    "current_skill": 0.5,
    "history": [],
    "drift_detected": False
}

# --- 2. DATA MODELS ---
class LoginRequest(BaseModel):
    username: str
    password: str

class AnswerSubmission(BaseModel):
    question_id: int
    user_answer: str
    time_taken_seconds: int

class FeedbackResponse(BaseModel):
    correct: bool
    explanation: str
    next_question: Optional[dict]
    skill_update: float
    drift_alert: bool

# --- 3. HELPER FUNCTIONS ---
def detect_drift(history):
    if len(history) < 2: return False
    recent = history[-2:]
    return all(not h['correct'] for h in recent)

def mock_rag_pipeline(topic: str):
    return f"[RAG Generated] Here is a simplified concept summary for {topic}..."

# --- 4. ENDPOINTS ---

@app.post("/login")
def login(creds: LoginRequest):
    # Simple mock authentication
    if creds.username == "admin" and creds.password == "password":
        # RESET state for a fresh demo
        user_state["current_skill"] = 0.5
        user_state["history"] = []
        user_state["drift_detected"] = False
        return {"message": "Login successful", "user": creds.username}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/get-question")
def get_next_question():
    target_difficulty = "medium"
    if user_state["drift_detected"] or user_state["current_skill"] < 0.4:
        target_difficulty = "easy"
    elif user_state["current_skill"] > 0.7:
        target_difficulty = "hard"
    
    candidates = [q for q in question_bank if q["difficulty"] == target_difficulty]
    if not candidates: candidates = question_bank 
    return random.choice(candidates)

@app.post("/submit", response_model=FeedbackResponse)
def submit_answer(submission: AnswerSubmission):
    question = next((q for q in question_bank if q["id"] == submission.question_id), None)
    if not question: raise HTTPException(status_code=404, detail="Question not found")
    
    is_correct = submission.user_answer.lower() == question["correct"].lower()
    
    user_state["history"].append({"correct": is_correct, "time": submission.time_taken_seconds})
    
    if is_correct: user_state["current_skill"] = min(1.0, user_state["current_skill"] + 0.1)
    else: user_state["current_skill"] = max(0.0, user_state["current_skill"] - 0.1)
        
    drift = detect_drift(user_state["history"])
    user_state["drift_detected"] = drift
    
    explanation = "Correct!"
    if not is_correct:
        explanation = f"Drift Detected! {mock_rag_pipeline(question['topic'])}" if drift else f"Incorrect. The right answer is {question['correct']}."

    return {
        "correct": is_correct,
        "explanation": explanation,
        "next_question": get_next_question(),
        "skill_update": user_state["current_skill"],
        "drift_alert": drift
    }