import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import InputText, User
from pydantic import BaseModel
from .oauth import router as oauth_router
from .auth import get_current_user
from starlette.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# Run DB migrations if needed using Alembic
# Assuming alembic set up, you'd run: alembic upgrade head before starting
Base.metadata.create_all(bind=engine)

app = FastAPI()

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN")
print("FRONTEND_ORIGIN: ", FRONTEND_ORIGIN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextInput(BaseModel):
    text: str

@app.post("/submit")
def submit_text(data: TextInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # This endpoint now requires authentication
    new_entry = InputText(text=data.text, owner_id=current_user.id)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {"message": "Text stored successfully", "id": new_entry.id}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    # Return basic user info
    return {"id": current_user.id, "username": current_user.username, "avatar_url": current_user.avatar_url}

# Include OAuth router
app.include_router(oauth_router)

# Serve frontend
# After building the frontend (npm run build), the `dist` folder will be created in frontend/
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

