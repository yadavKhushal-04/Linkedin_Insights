from fastapi import FastAPI
from app.api.routes import pages

app = FastAPI(title="Linkedin_Insights Microservice")
app.include_router(pages.router)

@app.get("/")
def root():
    return {
        "message": "Linkedin_Insights api is running"
    }