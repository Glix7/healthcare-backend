# Healthcare Backend API

A REST API for managing patients, doctors and patient-doctor assignments, built with Django, Django REST Framework, PostgreSQL and JWT authentication.

## Technology Stack

- Python 3.14, Django 6.1, Django REST Framework
- PostgreSQL (via `psycopg2-binary`)
- JWT authentication (`djangorestframework-simplejwt`)
- Environment variables via `python-decouple`

## Features

- User registration and JWT login (passwords hashed with Django's auth system)
- Patient CRUD, restricted to the user who created the record
- Doctor CRUD for any authenticated user
- Patient-doctor mappings with duplicate prevention (database constraint + validation)
- Ownership checks: users cannot view, change or map another user's patients
- Consistent JSON errors with proper HTTP status codes

## Project Structure

```
healthcare_backend/
├── config/        # settings, root URLs, automated tests (tests.py)
├── accounts/      # register, login, token refresh
├── patients/      # Patient model, serializer, views
├── doctors/       # Doctor model, serializer, views
├── mappings/      # PatientDoctorMapping model, serializer, views
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

## Installation (Windows)

Run these in PowerShell from the folder where you want the project.

```powershell
git clone <your-repo-url> healthcare_backend
cd healthcare_backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks the activation script, run once:
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

## PostgreSQL Setup

1. Install PostgreSQL from https://www.postgresql.org/download/windows/ (remember the `postgres` superuser password).
2. Open `psql` and create the database and user:

```powershell
& "C:\Program Files\PostgreSQL\<version>\bin\psql.exe" -U postgres -h localhost
```

```sql
CREATE USER healthcare_user WITH PASSWORD 'your_password_here';
CREATE DATABASE healthcare_db OWNER healthcare_user;
ALTER USER healthcare_user CREATEDB;
\q
```

`CREATEDB` is needed so Django can create a temporary database when running tests.

## Environment Variables

Copy `.env.example` to `.env` and fill in real values:

```powershell
Copy-Item .env.example .env
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for local development |
| `ALLOWED_HOSTS` | Comma separated hosts |
| `USE_POSTGRES` | `True` to use PostgreSQL (default setup) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection |

Generate a secret key with:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Migrations and Running the Server

```powershell
python manage.py migrate
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/`.

## Authentication (JWT)

1. Register, then log in to get tokens.
2. Send the access token on every protected request:

```
Authorization: Bearer <access_token>
```

Access tokens last 60 minutes. Use `POST /api/auth/token/refresh/` with `{"refresh": "<refresh_token>"}` to get a new access token.

## API Endpoints

All endpoints except register and login require the `Authorization` header.

### Auth

| Method | URL | Body | Success |
|---|---|---|---|
| POST | `/api/auth/register/` | `name`, `email`, `password` | 201 |
| POST | `/api/auth/login/` | `email`, `password` | 200 (`access`, `refresh`) |
| POST | `/api/auth/token/refresh/` | `refresh` | 200 |

Errors: 400 (validation, duplicate email), 401 (invalid credentials).

### Patients (owner only)

| Method | URL | Description | Success |
|---|---|---|---|
| POST | `/api/patients/` | Create a patient | 201 |
| GET | `/api/patients/` | List your patients | 200 |
| GET | `/api/patients/<id>/` | Retrieve one | 200 |
| PUT | `/api/patients/<id>/` | Update | 200 |
| DELETE | `/api/patients/<id>/` | Delete | 204 |

Body fields: `name`, `age`, `gender` (`male`/`female`/`other`), `phone`, `address`, `medical_history`.
Another user's patient returns 404.

### Doctors (any authenticated user)

| Method | URL | Description | Success |
|---|---|---|---|
| POST | `/api/doctors/` | Create a doctor | 201 |
| GET | `/api/doctors/` | List all doctors | 200 |
| GET | `/api/doctors/<id>/` | Retrieve one | 200 |
| PUT | `/api/doctors/<id>/` | Update | 200 |
| DELETE | `/api/doctors/<id>/` | Delete | 204 |

Body fields: `name`, `specialization`, `email` (unique), `phone`, `experience_years`.

### Mappings

| Method | URL | Description | Success |
|---|---|---|---|
| POST | `/api/mappings/` | Assign a doctor to your patient (`patient`, `doctor` IDs) | 201 |
| GET | `/api/mappings/` | List mappings of your patients | 200 |
| GET | `/api/mappings/<patient_id>/` | Doctors assigned to that patient | 200 |
| DELETE | `/api/mappings/<id>/` | Remove a mapping (by mapping ID) | 204 |

Notes:
- The same URL pattern is used for two purposes as specified: `GET` treats the number as a patient ID, `DELETE` treats it as a mapping ID. Each doctor in the `GET` response includes a `mapping_id` for deletion.
- Duplicate assignment, unknown patient/doctor, or a patient you do not own returns 400.

## Example Requests (PowerShell)

```powershell
# Register
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/auth/register/ -Method Post -ContentType "application/json" -Body (@{ name = "Test User"; email = "test@example.com"; password = "StrongPass@123" } | ConvertTo-Json)

# Login and keep the token
$login = Invoke-RestMethod -Uri http://127.0.0.1:8000/api/auth/login/ -Method Post -ContentType "application/json" -Body (@{ email = "test@example.com"; password = "StrongPass@123" } | ConvertTo-Json)
$headers = @{ Authorization = "Bearer $($login.access)" }

# Create a patient
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/patients/ -Method Post -Headers $headers -ContentType "application/json" -Body (@{ name = "Ramesh Kumar"; age = 45; gender = "male" } | ConvertTo-Json)
```

The same requests work in Postman: set the method and URL, add the header `Authorization: Bearer <access_token>`, and send a raw JSON body.

## Running the Tests

```powershell
python manage.py test --noinput
```

The suite (22 tests in `config/tests.py`) covers registration, login, authentication, patient ownership, doctor CRUD, mapping creation, duplicates, invalid IDs and deletion. It runs against PostgreSQL using a temporary test database.
