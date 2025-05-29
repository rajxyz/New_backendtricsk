from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routes.tricks import router as tricks_router           # Old 3 categories
from routes.new_tricks import router as new_tricks_router   # New 2 categories
from routes.search import router as search_router

app = FastAPI(title="Trick Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(tricks_router)        # old
app.include_router(new_tricks_router)    # new
app.include_router(search_router)

@app.get("/")
def home():
    return {"message": "Welcome to the Trick Generator API"}
