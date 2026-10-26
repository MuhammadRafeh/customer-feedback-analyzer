from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI, chat
from codespaces_blank.models import UserReview, FeedbackAnalysis

load_dotenv()

app = FastAPI()
client = OpenAI()

@app.get("/")
def root():
    return {"message": "This is Customer Feedback Analyzer Project"}

@app.post("/analyze", response_model=FeedbackAnalysis)
def analyze_feedback(review: UserReview):
    response = client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Analyze the customer feedback. "
                    "Classify it as positive, negative, or neutral. "
                    "Give an integer score from 1 to 5, where "
                    "1 is very negative and 5 is very positive. "
                    "The theme must be exactly one lowercase word."
                ),
            },
            {
                "role": "user",
                "content": f"This is a review: {review.text}",
            },
        ],
        response_format=FeedbackAnalysis,
    )

    result = response.choices[0].message.parsed

    if result is None:
        raise ValueError("The model did not return a parsed response.")

    return result