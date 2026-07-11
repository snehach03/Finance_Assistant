from pydantic import BaseModel
from typing import List, Optional


class QuestionRequest(BaseModel):
    question: str


class TransactionInput(BaseModel):
    dates: List[str]
    descriptions: List[str]
    amounts: List[float]
    types: List[str]


class CategorizeRequest(BaseModel):
    transactions: TransactionInput


class SummaryRequest(BaseModel):
    transactions: TransactionInput