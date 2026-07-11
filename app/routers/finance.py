from fastapi import APIRouter
import pandas as pd

from app.models.schemas import QuestionRequest, CategorizeRequest, SummaryRequest
from app.services.analytics_service import compute_analytics
from app.services.gemini_service import (
    categorize_transactions_batch,
    generate_ai_summary,
    ask_finance_question,
)

router = APIRouter()

class AskRequest(BaseModel):
    question: str
    transactions: TransactionInput


def build_dataframe(transactions):
    data = {
        "dates": transactions.dates,
        "descriptions": transactions.descriptions,
        "amounts": transactions.amounts,
        "types": transactions.types,
    }
    return pd.DataFrame(data)


@router.post("/categorize")
def categorize(request: CategorizeRequest):
    df = build_dataframe(request.transactions)
    unique_descriptions = df["descriptions"].unique().tolist()
    mapping = categorize_transactions_batch(unique_descriptions)

    if mapping is None:
        return {"error": "Sorry, the AI service is temporarily busy. Please try again in a moment."}

    df["category"] = df["descriptions"].map(mapping)
    return {"categories": df[["descriptions", "category"]].to_dict(orient="records")}


@router.post("/summary")
def summary(request: SummaryRequest):
    df = build_dataframe(request.transactions)
    analytics = compute_analytics(df)
    ai_summary = generate_ai_summary(analytics)
    return {"summary": ai_summary}


@router.post("/ask")
def ask(request: QuestionRequest, transactions: CategorizeRequest):
    df = build_dataframe(transactions.transactions)

    unique_descriptions = df["descriptions"].unique().tolist()
    mapping = categorize_transactions_batch(unique_descriptions)
    if mapping:
        df["category"] = df["descriptions"].map(mapping)

    analytics = compute_analytics(df)
    answer = ask_finance_question(request.question, analytics, df)
    return {"answer": answer}


@router.get("/health")
def health():
    return {"status": "ok"}