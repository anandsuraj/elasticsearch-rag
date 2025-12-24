from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from openai import OpenAI
from threading import Lock

# Load environment variables
load_dotenv()

# Initialize Elasticsearch and OpenAI clients
es_client = Elasticsearch(
    os.getenv("URL"),
    api_key=os.getenv("API_KEY")
)
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# FastAPI app
app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory storage for question history
question_history = []
# Thread-safe lock for question history
history_lock = Lock()

# Store question history in a file
HISTORY_FILE = "question_history.txt"

# Load existing history from file (if any) - keep only last 20
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        question_history = [line.strip() for line in f.readlines()]
        question_history = question_history[-20:]  # Keep only last 20

# Define request and response models
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    question: str
    answer: str

class HistoryResponse(BaseModel):
    history: List[str]

# Helper functions
def get_elasticsearch_results(query):
    es_query = {
        "retriever": {
            "standard": {
                "query": {
                    "semantic": {
                        "field": "text",
                        "query": query
                    }
                }
            }
        },
        "highlight": {
            "fields": {
                "text": {
                    "type": "semantic",
                    "number_of_fragments": 2,
                    "order": "score"
                }
            }
        },
        "size": 10
    }
    result = es_client.search(index="msmarco-semantic", body=es_query)
    return result["hits"]["hits"]

def create_openai_prompt(results):
    context = ""
    for hit in results:
        if "highlight" in hit:
            highlighted_texts = []
            for values in hit["highlight"].values():
                highlighted_texts.extend(values)
            context += "\n --- \n".join(highlighted_texts)
        else:
            context += hit["_source"].get("text", "")
    prompt = f"""
    Instructions:
    - You are an assistant for question-answering tasks.
    - Answer questions truthfully and factually using only the context presented.
    - If you don't know the answer, just say that you don't know, don't make up an answer.
    - Use markdown format for code examples.
    - You are correct, factual, precise, and reliable.

    Context:
    {context}
    """
    return prompt

def generate_openai_completion(user_prompt, question):
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": user_prompt},
            {"role": "user", "content": question},
        ]
    )
    return response.choices[0].message.content

# API Endpoints
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    question = request.question

    # Get Elasticsearch results
    try:
        elasticsearch_results = get_elasticsearch_results(question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticsearch error: {str(e)}")

    # Create OpenAI prompt
    context_prompt = create_openai_prompt(elasticsearch_results)

    # Generate OpenAI completion
    try:
        answer = generate_openai_completion(context_prompt, question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    # Store question in history (thread-safe) - keep only last 20
    with history_lock:
        question_history.append(question)
        # Keep only last 20 questions
        if len(question_history) > 20:
            question_history.pop(0)
        # Rewrite file with last 20 questions
        with open(HISTORY_FILE, "w") as f:
            for q in question_history:
                f.write(q + "\n")

    return AnswerResponse(question=question, answer=answer)

@app.get("/history", response_model=HistoryResponse)
def get_history():
    return HistoryResponse(history=question_history)

# Run the app
# To run: uvicorn fastapi_rag_app:app --reload