from fastapi import FastAPI
from app.routers import finance

app = FastAPI(title="AI Personal Finance Assistant")

app.include_router(finance.router)


@app.get("/")
def root():
    return {"message": "AI Personal Finance Assistant API is running"}