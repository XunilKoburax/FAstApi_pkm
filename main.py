import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Pokedex API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Load JSON Data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "pokedex.json")

try:
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        pokemon_data = json.load(file)
except Exception as e:
    pokemon_data = []

@app.get("/api/pokemon/name/{name}")
def get_pokemon_by_name(name: str):
    for pkm in pokemon_data:
        # Assuming the structure is: "name": {"english": "Bulbasaur", ...}
        # Based on typical pokedex structures and previous requirements
        pkm_name = pkm.get("name", {})
        if isinstance(pkm_name, dict):
            english_name = pkm_name.get("english", "")
        else:
            english_name = str(pkm_name)
            
        if english_name.lower() == name.lower():
            # Clone to avoid mutating global dictionary
            response_pkm = dict(pkm)
            response_pkm["name"] = english_name
            return response_pkm
            
    raise HTTPException(status_code=404, detail="Pokemon not found")

@app.get("/api/pokemon/type/{tipo}")
def get_pokemon_by_type(tipo: str):
    result = []
    search_type = tipo.lower()
    for pkm in pokemon_data:
        types = [t.lower() for t in pkm.get("type", [])]
        if search_type in types:
            result.append(pkm)
    return result

@app.get("/api/pokemon/attack/{attack}")
def get_pokemon_by_attack(attack: int):
    result = []
    for pkm in pokemon_data:
        base = pkm.get("base", {})
        if base.get("Attack") == attack:
            result.append(pkm)
    return result
