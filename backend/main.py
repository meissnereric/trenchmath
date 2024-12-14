import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from .database import Base, engine, get_db
from .models import InputText, User
from .oauth import router as oauth_router
from .auth import get_current_user
from .warband_lore import generate_warband_lore
# Import your Trench Crusade math functions here:
from .trench_crusade_math import (
    compute,
    compute_success_distribution,
    compute_injury_outcome_refined,
    plot_distributions_with_out_of_action_fixed,
    injury_thresholds
)

load_dotenv()

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
    # Requires login for now
    new_entry = InputText(text=data.text, owner_id=current_user.id)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {"message": "Text stored successfully", "id": new_entry.id}

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
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
    hit_distribution: dict[int, float]
    injury_params: dict[str, int | bool]

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
    injury_params = req.injury_params
    # Ensure extra_d6 is bool
    if isinstance(injury_params.get("extra_d6"), str):
        injury_params["extra_d6"] = (injury_params["extra_d6"].lower() == "true")

    result = compute_injury_outcome_refined(req.hit_distribution, injury_params, injury_thresholds)
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

@app.post("/warband_lore")
def save_warband_lore(lore: dict):
    print("Received Warband Lore:", lore)
    return {"message": "saved warband"}


class WarbandLoreRequest(BaseModel):
    warband_text: str
    theme_info: Optional[str] = None

@app.post("/warband_lore/generate")
def warband_lore_generate(req: WarbandLoreRequest):
    lore = generate_warband_lore(req.warband_text, req.theme_info)
    return lore

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
