import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class SpanishNameUpdate(BaseModel):
    spanish_name: str

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

@app.patch("/api/pokemon/name/{name}/spanish")
def update_spanish_name(name: str, data: SpanishNameUpdate):
    """
    Actualiza el nombre en español de un Pokemon y lo guarda en el JSON.
    Se utiliza PATCH porque estamos aplicando una modificación parcial a un recurso.
    """
    found = False
    updated_pkm = None
    for pkm in pokemon_data:
        pkm_name = pkm.get("name", {})
        if isinstance(pkm_name, dict):
            english_name = pkm_name.get("english", "")
        else:
            english_name = str(pkm_name)
            
        if english_name.lower() == name.lower():
            if isinstance(pkm_name, dict):
                pkm["name"]["spanish"] = data.spanish_name
            else:
                pkm["name"] = {"english": english_name, "spanish": data.spanish_name}
            
            found = True
            updated_pkm = pkm
            break
            
    if not found:
        raise HTTPException(status_code=404, detail="Pokemon no encontrado")
        
    try:
        with open(JSON_PATH, "w", encoding="utf-8") as file:
            json.dump(pokemon_data, file, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando los datos: {str(e)}")
        
    return {"message": "Nombre en español actualizado exitosamente", "pokemon": updated_pkm}
