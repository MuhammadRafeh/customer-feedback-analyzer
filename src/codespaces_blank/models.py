from pydantic import BaseModel

class UserReview(BaseModel):
    text: str

class FeedbackAnalysis(BaseModel):
    label: str
    score: int
    theme: str