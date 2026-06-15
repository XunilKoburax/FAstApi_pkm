import json
import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from auth.router import router as auth_router
from auth.security import JWTBearer, get_current_user, require_admin
from database import init_db, get_db_connection, sync_db_to_json

class SpanishNameUpdate(BaseModel):
    spanish_name: str

class ProfileUpdate(BaseModel):
    name: str = None
    password: str = None

class AddPokemonRequest(BaseModel):
    pokemon_id: int

class TrainerCreate(BaseModel):
    username: str
    password: str
    name: str

class TrainerUpdate(BaseModel):
    username: str = None
    password: str = None
    name: str = None

app = FastAPI(title="Pokedex API")

@app.on_event("startup")
def startup_db():
    init_db()

app.include_router(auth_router)


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

@app.get("/api/secure/pokemon/search", dependencies=[Depends(JWTBearer())])
def secure_search_pokemon(name: str):
    """
    Ruta protegida para buscar un pokemon por nombre usando un parámetro de consulta (?name=...).
    Requiere token JWT de autenticación.
    """
    for pkm in pokemon_data:
        pkm_name = pkm.get("name", {})
        if isinstance(pkm_name, dict):
            english_name = pkm_name.get("english", "")
        else:
            english_name = str(pkm_name)
            
        if english_name.lower() == name.lower():
            return pkm
            
    raise HTTPException(status_code=404, detail="Pokemon no encontrado")


# ==========================================
# RUTAS DE PERFIL DE USUARIO
# ==========================================

@app.get("/api/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Retorna el perfil del usuario autenticado y los detalles de su equipo Pokémon.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pokemon_id FROM teams WHERE user_id = ?", (current_user["id"],))
    team_rows = cursor.fetchall()
    team_ids = [row["pokemon_id"] for row in team_rows]
    conn.close()
    
    # Resolver detalles del pokemon desde pokedex.json
    team_details = []
    for p_id in team_ids:
        pkm = next((p for p in pokemon_data if p.get("id") == p_id), None)
        if pkm:
            team_details.append(pkm)
            
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "name": current_user["name"],
        "role": current_user["role"],
        "team_ids": team_ids,
        "team_details": team_details
    }

@app.put("/api/profile")
def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """
    Permite al usuario actualizar su nombre y/o contraseña.
    """
    if not data.name and not data.password:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un campo para actualizar (name o password).")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if data.name and data.password:
        cursor.execute("UPDATE users SET name = ?, password = ? WHERE id = ?", (data.name, data.password, current_user["id"]))
    elif data.name:
        cursor.execute("UPDATE users SET name = ? WHERE id = ?", (data.name, current_user["id"]))
    elif data.password:
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (data.password, current_user["id"]))
        
    conn.commit()
    conn.close()
    
    sync_db_to_json()
    return {"message": "Perfil actualizado exitosamente."}


# ==========================================
# RUTAS DE GESTIÓN DE EQUIPOS POKÉMON
# ==========================================

@app.post("/api/team/add")
def add_pokemon_to_team(req: AddPokemonRequest, current_user: dict = Depends(get_current_user)):
    """
    Agrega un Pokémon (por ID) al equipo del usuario autenticado (Límite: 6 Pokémon).
    """
    # Verificar que el usuario tenga rol de 'user'
    if current_user["role"] != "user":
        raise HTTPException(status_code=403, detail="Solo los entrenadores pueden tener un equipo Pokémon.")
        
    # Verificar si el Pokémon existe en pokedex.json
    pokemon_exists = any(p.get("id") == req.pokemon_id for p in pokemon_data)
    if not pokemon_exists:
        raise HTTPException(status_code=404, detail="El Pokémon con el ID especificado no existe en el Pokedex.")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar límite de equipo (máximo 6)
    cursor.execute("SELECT COUNT(*) FROM teams WHERE user_id = ?", (current_user["id"],))
    current_count = cursor.fetchone()[0]
    if current_count >= 6:
        conn.close()
        raise HTTPException(status_code=400, detail="El equipo ya tiene el límite máximo de 6 Pokémon.")
        
    cursor.execute("INSERT INTO teams (user_id, pokemon_id) VALUES (?, ?)", (current_user["id"], req.pokemon_id))
    conn.commit()
    conn.close()
    
    sync_db_to_json()
    return {"message": f"Pokémon con ID {req.pokemon_id} agregado al equipo exitosamente."}

@app.delete("/api/team/remove/{pokemon_id}")
def remove_pokemon_from_team(pokemon_id: int, current_user: dict = Depends(get_current_user)):
    """
    Elimina un Pokémon (por ID) del equipo del usuario autenticado.
    """
    if current_user["role"] != "user":
        raise HTTPException(status_code=403, detail="Solo los entrenadores pueden gestionar su equipo Pokémon.")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si el Pokémon está en el equipo
    cursor.execute("SELECT id FROM teams WHERE user_id = ? AND pokemon_id = ? LIMIT 1", (current_user["id"], pokemon_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="El Pokémon no está en el equipo del usuario.")
        
    # Eliminar solo una instancia (por si hay duplicados)
    cursor.execute("DELETE FROM teams WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    
    sync_db_to_json()
    return {"message": f"Pokémon con ID {pokemon_id} eliminado del equipo."}


# ==========================================
# RUTAS DE ADMINISTRADOR (GESTIÓN DE ENTRENADORES)
# ==========================================

@app.get("/api/admin/trainers")
def get_trainers(current_admin: dict = Depends(require_admin)):
    """
    Retorna la lista de todos los entrenadores (usuarios con rol 'user') y sus equipos.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, role FROM users WHERE role = 'user'")
    trainers = cursor.fetchall()
    
    result = []
    for t in trainers:
        t_id = t["id"]
        cursor.execute("SELECT pokemon_id FROM teams WHERE user_id = ?", (t_id,))
        team_rows = cursor.fetchall()
        team_ids = [row["pokemon_id"] for row in team_rows]
        
        result.append({
            "id": t_id,
            "username": t["username"],
            "name": t["name"],
            "role": t["role"],
            "team": team_ids
        })
        
    conn.close()
    return result

@app.post("/api/admin/trainers", status_code=status.HTTP_201_CREATED)
def create_trainer(data: TrainerCreate, current_admin: dict = Depends(require_admin)):
    """
    Permite al administrador agregar un nuevo entrenador.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si el nombre de usuario ya está tomado
    cursor.execute("SELECT id FROM users WHERE username = ?", (data.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso.")
        
    cursor.execute(
        "INSERT INTO users (username, password, role, name) VALUES (?, ?, 'user', ?)",
        (data.username, data.password, data.name)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    sync_db_to_json()
    return {
        "message": "Entrenador creado exitosamente.",
        "trainer": {
            "id": new_id,
            "username": data.username,
            "name": data.name,
            "role": "user"
        }
    }

@app.put("/api/admin/trainers/{trainer_id}")
def update_trainer(trainer_id: int, data: TrainerUpdate, current_admin: dict = Depends(require_admin)):
    """
    Permite al administrador actualizar los datos de un entrenador.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el entrenador existe y es rol 'user'
    cursor.execute("SELECT id, username FROM users WHERE id = ? AND role = 'user'", (trainer_id,))
    trainer = cursor.fetchone()
    if not trainer:
        conn.close()
        raise HTTPException(status_code=404, detail="Entrenador no encontrado.")
        
    if not data.username and not data.password and not data.name:
        conn.close()
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un campo para actualizar (username, password o name).")
        
    if data.username and data.username != trainer["username"]:
        # Verificar que el nuevo username no esté tomado
        cursor.execute("SELECT id FROM users WHERE username = ?", (data.username,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="El nuevo nombre de usuario ya está en uso.")
            
    # Construir consulta dinámica de actualización
    fields = []
    params = []
    if data.username:
        fields.append("username = ?")
        params.append(data.username)
    if data.password:
        fields.append("password = ?")
        params.append(data.password)
    if data.name:
        fields.append("name = ?")
        params.append(data.name)
        
    params.append(trainer_id)
    query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, tuple(params))
    conn.commit()
    conn.close()
    
    sync_db_to_json()
    return {"message": "Datos del entrenador actualizados exitosamente."}

@app.delete("/api/admin/trainers/{trainer_id}")
def delete_trainer(trainer_id: int, current_admin: dict = Depends(require_admin)):
    """
    Permite al administrador eliminar un entrenador (y en cascada su equipo).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el entrenador existe y es rol 'user'
    cursor.execute("SELECT id FROM users WHERE id = ? AND role = 'user'", (trainer_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Entrenador no encontrado.")
        
    cursor.execute("DELETE FROM users WHERE id = ?", (trainer_id,))
    conn.commit()
    conn.close()
    
    sync_db_to_json()
    return {"message": "Entrenador eliminado exitosamente de la base de datos y archivo de persistencia."}


