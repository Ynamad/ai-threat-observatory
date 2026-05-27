from fastapi import FastAPI
from app.api.routes import router


app = FastAPI(
    title="AI Threat Observatory",
    description="AI-assisted vulnerability enrichment and semantic similarity service.",
    version="0.1.0",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "AI Threat Observatory",
        "status": "running",
        "version": "0.1.0",
    }