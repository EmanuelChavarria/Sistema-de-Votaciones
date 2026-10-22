# API de Sistema de Votaciones

API RESTful para gestionar un sistema de votaciones: registro de votantes y candidatos, emisión de votos (un único voto por votante) y estadísticas de resultados. Protegida con **JWT** y documentada con **Swagger**.

## Tecnologías

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0
- SQLite (por defecto) o PostgreSQL (opcional, con Docker)
- Pydantic v2
- JWT (PyJWT) + bcrypt
- Pytest

## Requisitos previos

- Python 3.11 o superior
- Git
- (Opcional) [Docker Desktop](https://www.docker.com/products/docker-desktop/), solo si quieres usar PostgreSQL en lugar de SQLite

## Ejecución local

### 1. Clonar el repositorio

```bash
git clone https://github.com/EmanuelChavarria/Sistema-de-Votaciones
cd Sistema-de-Votaciones
```

### 2. Crear el entorno virtual e instalar dependencias

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configurar variables de entorno y base de datos

Copia la plantilla de variables de entorno:

```bash
# Linux / macOS / Git Bash
cp .env.example .env

# Windows (CMD o PowerShell)
copy .env.example .env
```

#### 3.1 Generar la clave secreta (`SECRET_KEY`)

La API firma los tokens JWT con la variable `SECRET_KEY`. Quien conozca esa clave podría fabricar tokens válidos, así que **debe ser un valor largo, aleatorio y privado**. Genera una con este comando:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

¿Qué hace?

- `python -c "..."` ejecuta una línea de código Python sin crear un archivo.
- `import secrets` carga el módulo de Python diseñado para generar valores aleatorios seguros para uso criptográfico.
- `secrets.token_hex(32)` genera 32 bytes aleatorios y los muestra en hexadecimal: una cadena de 64 caracteres, por ejemplo `9f2c...e41b`.
- `print(...)` muestra el resultado en pantalla.

Copia el resultado y pégalo en tu archivo `.env`:

```
SECRET_KEY=9f2c...e41b
```

Recomendaciones:

- Cada persona o entorno debe generar **su propia clave**.
- **No subas el `.env` a GitHub** (ya está en el `.gitignore`). Solo se versiona `.env.example`, que no contiene claves reales.
- Si cambias la clave, los tokens emitidos antes dejan de ser válidos y hay que iniciar sesión de nuevo.

#### 3.2 Elegir la base de datos

Elige **una** de las dos opciones editando `DATABASE_URL` en tu `.env`.

**Opción A: SQLite (por defecto, recomendada para probar rápido)**

No necesitas instalar nada más. Deja esta línea en tu `.env`:

```
DATABASE_URL=sqlite:///./votaciones.db
```

Se creará automáticamente el archivo `votaciones.db` en la carpeta del proyecto.

**Opción B: PostgreSQL con Docker (opcional)**

Requiere tener Docker instalado y en ejecución. Levanta la base de datos:

```bash
docker compose up -d
```

Y cambia `DATABASE_URL` en tu `.env`:

```
DATABASE_URL=postgresql+psycopg2://votaciones:votaciones@localhost:5432/votaciones
```

> Si al ejecutar `docker compose up -d` aparece que el comando no se reconoce, Docker no está instalado o no está en el PATH. Instálalo desde el enlace de arriba, reinicia la terminal, o usa la Opción A.

### 4. Iniciar la API

```bash
uvicorn app.main:app --reload
```

Las tablas se crean automáticamente al iniciar.

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

> **Si el puerto 8000 está ocupado** (en Windows puede aparecer `WinError 10013`), usa otro puerto: `uvicorn app.main:app --reload --port 8001`. En ese caso cambia también el puerto en las URLs de este documento.

## Autenticación (JWT)

Todos los endpoints de `/voters`, `/candidates` y `/votes` requieren un token. Solo `/auth/register`, `/auth/login` y `/health` son públicos.

### Desde Swagger

1. Abre http://localhost:8000/docs
2. Ejecuta `POST /auth/register` para crear un usuario.
3. Pulsa el botón **Authorize**, escribe tu `username` y `password` y confirma.
4. Ya puedes probar todos los endpoints protegidos.

### Desde curl

```bash
# Registrar usuario
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin12345"}'

# Iniciar sesión (form-data) y obtener el token
curl -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=Admin12345"
```

Respuesta:

```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer" }
```

En los ejemplos siguientes reemplaza `<TOKEN>` por el valor de `access_token`. El token expira a los 60 minutos; si recibes un `401`, vuelve a iniciar sesión.

### Nota para Windows PowerShell

En PowerShell, `curl` es un alias de otro comando y las comillas del JSON se interpretan de forma distinta. Hay dos opciones:

1. Usar `curl.exe` (con `.exe`), todo en una sola línea y el JSON desde un archivo:

   ```powershell
   '{"username": "admin", "password": "Admin12345"}' | Out-File -Encoding ascii register.json
   curl.exe -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" -d "@register.json"
   ```

2. Usar el comando nativo `Invoke-RestMethod`:

   ```powershell
   Invoke-RestMethod -Method Post -Uri http://localhost:8000/auth/register -ContentType "application/json" -Body '{"username": "admin", "password": "Admin12345"}'
   ```

Alternativamente, usa Git Bash o Swagger (`/docs`), donde los ejemplos de este documento funcionan tal cual.

## Endpoints

| Método | Ruta | Descripción | Códigos |
|---|---|---|---|
| POST | `/auth/register` | Registrar usuario | 201, 409, 422 |
| POST | `/auth/login` | Obtener token JWT | 200, 401 |
| POST | `/voters` | Registrar votante | 201, 409, 422 |
| GET | `/voters` | Listar votantes (filtros y paginación) | 200 |
| GET | `/voters/{id}` | Detalle de un votante | 200, 404 |
| DELETE | `/voters/{id}` | Eliminar votante | 204, 404, 409 |
| POST | `/candidates` | Registrar candidato | 201, 409, 422 |
| GET | `/candidates` | Listar candidatos (filtros y paginación) | 200 |
| GET | `/candidates/{id}` | Detalle de un candidato | 200, 404 |
| DELETE | `/candidates/{id}` | Eliminar candidato | 204, 404, 409 |
| POST | `/votes` | Emitir un voto | 201, 404, 409, 422 |
| GET | `/votes` | Listar votos | 200 |
| GET | `/votes/statistics` | Estadísticas de la votación | 200 |
| GET | `/health` | Estado del servicio | 200 |

Todos los endpoints protegidos pueden responder además `401` si falta el token o es inválido.

## Ejemplos de uso

### Votantes

```bash
# Crear votante
curl -X POST http://localhost:8000/voters \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Ana Torres", "email": "ana@example.com"}'

# Listar con filtros y paginación
curl "http://localhost:8000/voters?page=1&page_size=10&has_voted=false&search=ana" \
  -H "Authorization: Bearer <TOKEN>"

# Detalle
curl http://localhost:8000/voters/1 -H "Authorization: Bearer <TOKEN>"

# Eliminar
curl -X DELETE http://localhost:8000/voters/1 -H "Authorization: Bearer <TOKEN>"
```

### Candidatos

```bash
# Crear candidato
curl -X POST http://localhost:8000/candidates \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Carlos Ruiz", "party": "Partido Verde"}'

# Listar
curl "http://localhost:8000/candidates?page=1&page_size=10" \
  -H "Authorization: Bearer <TOKEN>"

# Detalle
curl http://localhost:8000/candidates/1 -H "Authorization: Bearer <TOKEN>"

# Eliminar
curl -X DELETE http://localhost:8000/candidates/1 -H "Authorization: Bearer <TOKEN>"
```

### Votos

```bash
# Emitir voto
curl -X POST http://localhost:8000/votes \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"voter_id": 1, "candidate_id": 1}'

# Listar votos
curl http://localhost:8000/votes -H "Authorization: Bearer <TOKEN>"

# Estadísticas
curl http://localhost:8000/votes/statistics -H "Authorization: Bearer <TOKEN>"
```

Respuesta de ejemplo de `/votes/statistics`:

```json
{
  "total_votes": 10,
  "total_voters_registered": 25,
  "total_voters_who_voted": 10,
  "participation_percentage": 40.0,
  "candidates": [
    { "candidate_id": 2, "name": "Carlos Ruiz", "party": "Partido Verde", "votes": 6, "percentage": 60.0 },
    { "candidate_id": 1, "name": "Laura Gómez", "party": null, "votes": 4, "percentage": 40.0 },
    { "candidate_id": 3, "name": "Pedro Díaz", "party": "Independiente", "votes": 0, "percentage": 0.0 }
  ]
}
```

### Ejemplo de error

Votar dos veces con el mismo votante:

```json
{ "detail": "El votante ya emitió su voto" }
```

## Capturas

### Estadísticas de la votación

![Estadísticas](docs/img/estadisticas.png)

### Swagger UI

![Swagger](docs/img/swagger.png)

## Reglas de negocio y decisiones de diseño

- **Un voto por votante:** se garantiza con tres capas: validación en el servicio, restricción `UNIQUE` sobre `votes.voter_id` y bloqueo de la fila del votante dentro de la transacción.
- **Atomicidad:** al votar, en una sola transacción se registra el voto, se marca `has_voted = true` y se incrementa `votes` del candidato. Si algo falla, no se aplica nada.
- **Votante ≠ candidato:** como el candidato no tiene email, se compara por **nombre normalizado** (sin espacios sobrantes y sin distinguir mayúsculas). Limitación: dos personas distintas con el mismo nombre no pueden ser una votante y otra candidata.
- **Eliminaciones:** no se puede eliminar un votante que ya votó ni un candidato con votos (409), para no alterar los resultados.
- **Estadísticas:** incluyen todos los candidatos (también los de 0 votos), ordenados por votos. Si no hay votos, los porcentajes son 0 (sin división por cero).
- **Errores:** respuestas con formato `{"detail": "mensaje"}` y códigos HTTP coherentes: 404 (no existe), 409 (conflicto de negocio), 401 (sin autenticación), 422 (datos inválidos).

## Pruebas

```bash
pytest -q
```

Las pruebas usan SQLite en memoria, por lo que no requieren Docker ni PostgreSQL. Cubren autenticación, votantes, candidatos, votos y estadísticas.

## Estructura del proyecto

```
app/
├── main.py            # Aplicación FastAPI y manejo de errores
├── core/              # Configuración, seguridad (JWT) y excepciones
├── db/                # Conexión y sesión de base de datos
├── models/            # Modelos SQLAlchemy
├── schemas/           # Esquemas Pydantic (entrada/salida)
├── services/          # Lógica de negocio
└── api/
    ├── deps.py        # Dependencia de autenticación
    └── routers/       # Endpoints (auth, voters, candidates, votes)
tests/                 # Pruebas automatizadas
docs/img/              # Capturas para el README
```

## Posibles mejoras

- Migraciones con Alembic
- Roles y permisos (administrador / auditor)
- Limitación de peticiones (rate limiting)
- Despliegue de la API con Docker en un servicio en la nube
