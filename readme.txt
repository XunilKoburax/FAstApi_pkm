# Proyecto FastAPI - API Pokémon

Este es un proyecto reconstruido en FastAPI configurado para funcionar como una API sin autenticación, consumiendo directamente el archivo `pokedex.json`. 

Está configurado con `CORSMiddleware` permitiendo solicitudes desde cualquier origen (`allow_origins=["*"]`) para facilitar su consumo desde Flutter u otras aplicaciones, idéntico al proyecto Django origen.

## Ejecutar el servidor
Para ejecutar el servidor en tu entorno de desarrollo, utiliza:

```bash
uvicorn main:app --reload
```

FastAPI provee documentación interactiva automática. Puedes visualizar los endpoints desde tu navegador y probarlos accediendo a:
- Swagger UI: `http://127.0.0.1:8000/docs`

## Rutas de la API

La base URL de la API (si corres el proyecto localmente) será normalmente `http://127.0.0.1:8000/`.

Todas las rutas configuradas son las siguientes:

### 1. Búsqueda por Nombre
**Ruta:** `/api/pokemon/name/<nombre>/`
**Ejemplo:** `http://127.0.0.1:8000/api/pokemon/name/Bulbasaur/`

**Descripción:**
Devuelve un objeto JSON con toda la información del Pokémon que coincida con el nombre introducido de forma exacta (sin importar mayúsculas o minúsculas). Al igual que la versión de Django, el objeto retornado transforma el campo "name" devolviendo únicamente el string equivalente al nombre en inglés.

### 2. Búsqueda por Tipo
**Ruta:** `/api/pokemon/type/<tipo>/`
**Ejemplo:** `http://127.0.0.1:8000/api/pokemon/type/fire/`

**Descripción:**
Busca y devuelve en formato de *array list* todos los Pokémon que contengan el tipo especificado.

### 3. Búsqueda por Ataque (Exacto)
**Ruta:** `/api/pokemon/attack/<ataque>/`
**Ejemplo:** `http://127.0.0.1:8000/api/pokemon/attack/49/`

**Descripción:**
Devuelve un *array list* con todos los Pokémon cuyo valor base de ataque sea exactamente igual al indicando en la URL.
