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

from database import get_db_connection

def check_user_db(data: UserLoginSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (data.username, data.password))
    user = cursor.fetchone()
    conn.close()
    return user

@router.post("/login")
async def user_login(user: UserLoginSchema):
    db_user = check_user_db(user)
    if db_user:
        return sign_jwt(db_user["username"], db_user["role"])
    raise HTTPException(status_code=401, detail="Wrong login details!")


@router.get("/protected", dependencies=[Depends(JWTBearer())])
async def protected_route():
    return {"message": "You are viewing this because you are an authenticated admin!"}

POKEDEX_FILE = os.path.join(os.path.dirname(__file__), "..", "pokedex.json")

try:
    with open(POKEDEX_FILE, "r", encoding="utf-8") as file:
        pokemon_data = json.load(file)
except Exception as e:
    pokemon_data = []

@router.get("/pokemon/search", dependencies=[Depends(JWTBearer())])
async def search_pokemon(name: str):
    for pkm in pokemon_data:
        pkm_name = pkm.get("name", {})
        if isinstance(pkm_name, dict):
            english_name = pkm_name.get("english", "")
        else:
            english_name = str(pkm_name)
            
        if english_name.lower() == name.lower():
            return pkm
            
    raise HTTPException(status_code=404, detail="Pokemon no encontrado")

