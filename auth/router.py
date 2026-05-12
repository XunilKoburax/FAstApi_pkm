import json
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .security import JWTBearer, sign_jwt

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserLoginSchema(BaseModel):
    username: str
    password: str

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def check_user(data: UserLoginSchema):
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users_db = json.load(f)
            for user in users_db.get("users", []):
                if user["username"] == data.username and user["password"] == data.password:
                    return True
    return False

@router.post("/login")
async def user_login(user: UserLoginSchema):
    if check_user(user):
        return sign_jwt(user.username)
    raise HTTPException(status_code=401, detail="Wrong login details!")

@router.get("/protected", dependencies=[Depends(JWTBearer())])
async def protected_route():
    return {"message": "You are viewing this because you are an authenticated admin!"}
