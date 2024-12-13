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


# Import your Trench Crusade math functions here:
# (We copy them from the given code)
from .trench_crusade_math import (
    compute,
    compute_success_distribution,
    compute_injury_outcome_refined,
    plot_distributions_with_out_of_action_fixed,
    injury_thresholds
)

load_dotenv()

# Run DB migrations if needed using Alembic
# Assuming alembic set up, you'd run: alembic upgrade head before starting
Base.metadata.create_all(bind=engine)

app = FastAPI()

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN")
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    FRONTEND_ORIGIN
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include OAuth router
app.include_router(oauth_router)


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

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    # Return basic user info
    return {"id": current_user.id, "username": current_user.username, "avatar_url": current_user.avatar_url}


class ComputeRequest(BaseModel):
    modified_dice: int = 0
    extra_d6: bool = False
    flat_modifier: int = 0

class SuccessDistributionRequest(BaseModel):
    modified_dice: int = 0
    extra_d6: bool = False
    flat_modifier: int = 0
    threshold: int = 7
    num_rolls: int = 1

class InjuryOutcomeRequest(BaseModel):
    hit_distribution: dict[int, float]  # {hits: probability}
    injury_params: dict[str, int]       # {modified_dice, extra_d6(bool?), flat_modifier}
    # We'll treat extra_d6 in injury_params as a bool as well.
    # Make sure to cast where needed.
    # example: {"modified_dice": -1, "extra_d6": true, "flat_modifier": -3}

@app.post("/compute_distribution")
def get_compute_distribution(req: ComputeRequest):
    dist = compute(req.modified_dice, req.extra_d6, req.flat_modifier)
    return {"distribution": dist}

@app.post("/compute_success_distribution")
def get_success_distribution(req: SuccessDistributionRequest):
    dist = compute_success_distribution(
        modified_dice=req.modified_dice,
        extra_d6=req.extra_d6,
        flat_modifier=req.flat_modifier,
        threshold=req.threshold,
        num_rolls=req.num_rolls
    )
    return {"success_distribution": dist}

@app.post("/compute_injury_outcome")
def get_injury_outcome(req: InjuryOutcomeRequest):
    # Convert extra_d6 back to bool if needed
    injury_params = req.injury_params
    if isinstance(injury_params.get("extra_d6"), str):
        injury_params["extra_d6"] = (injury_params["extra_d6"].lower() == "true")

    result = compute_injury_outcome_refined(req.hit_distribution, injury_params, injury_thresholds)
    # Return both distributions as lists for easy chart usage
    blood_markers = []
    blood_probs = []
    for bm, p in result["blood_marker_distribution"].items():
        blood_markers.append(bm)
        blood_probs.append(p)

    out_of_action_prob = result["out_of_action_probability"]
    return {
        "blood_marker_distribution": {
            "markers": blood_markers,
            "probabilities": blood_probs
        },
        "out_of_action_probability": out_of_action_prob
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Serve frontend
# After building the frontend (npm run build), the `dist` folder will be created in frontend/
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
