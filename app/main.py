from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import finance

app = FastAPI(title="AI Personal Finance Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(finance.router)


@app.get("/")
def root():
    return {"message": "AI Personal Finance Assistant API is running"}