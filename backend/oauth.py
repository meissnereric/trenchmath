import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .utils import create_jwt
from dotenv import load_dotenv

load_dotenv()

print("CWD:", os.getcwd())
print("DISCORD_REDIRECT_URI after load:", os.getenv("DISCORD_REDIRECT_URI"))

router = APIRouter()

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
DISCORD_OAUTH_AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_OAUTH_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_USER_URL = "https://discord.com/api/users/@me"
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN")

print("DISCORD_REDIRECT_URI:", DISCORD_REDIRECT_URI)

@router.get("/auth/discord/login")
def discord_login():
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
    }
    url = DISCORD_OAUTH_AUTHORIZE_URL + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return RedirectResponse(url)

@router.get("/auth/discord/callback")
async def discord_callback(code: str, db: Session = Depends(get_db)):
    # Exchange code for token
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(DISCORD_OAUTH_TOKEN_URL, data=data, headers=headers)
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get token from Discord")
        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        # Get user info
        user_resp = await client.get(DISCORD_API_USER_URL, headers={"Authorization": f"Bearer {access_token}"})
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info")
        user_data = user_resp.json()

    # Upsert the user in DB
    discord_id = user_data["id"]
    username = user_data["username"] + "#" + user_data["discriminator"]
    avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{user_data['avatar']}.png" if user_data.get("avatar") else None

    user = db.query(User).filter(User.discord_id == discord_id).first()
    if not user:
        user = User(discord_id=discord_id, username=username, avatar_url=avatar_url)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update info if needed
        user.username = username
        user.avatar_url = avatar_url
        db.commit()

    # Create JWT
    token = create_jwt({"sub": str(user.id)})

    # Redirect back to frontend with a session cookie
    response = RedirectResponse(FRONTEND_ORIGIN)
    response.set_cookie("access_token", value=token, httponly=True, secure=False, samesite="strict")
    return response

