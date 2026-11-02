# User Service

[![Python CI](https://github.com/noname1134/user_service/actions/workflows/ci.yml/badge.svg)](https://github.com/noname1134/user_service/actions/workflows/ci.yml)

A REST API for managing customer profiles and registration in a two-service polling system.

Built with **Python, FastAPI, and MySQL**, with **Docker Compose** for local deployment. The service integrates with [Poll Service](https://github.com/noname1134/poll_service) to remove a user's answers before deleting their profile.

## Features

- Create, retrieve, partially update, and delete customer profiles.
- Register users so they can participate in polls.
- Validate names, age, and timezone-aware joining dates with Pydantic.
- Normalize joining dates to UTC for database storage and API responses.
- Coordinate answer cleanup with the Poll Service during user deletion.
- Use parameterized SQL queries and an allowlist of update fields.
- Explore endpoints through interactive Swagger documentation.
- Verify API behavior and MySQL persistence with automated tests and GitHub Actions.

## Technology Stack

| Component | Technology |
| :--- | :--- |
| Language | Python |
| API framework | FastAPI |
| Validation | Pydantic |
| Database | MySQL 8.4 |
| Database driver | MySQL Connector/Python |
| HTTP client | HTTPX |
| Configuration | Environment variables and python-dotenv |
| Containers | Docker and Docker Compose |

## Architecture

The application separates HTTP handling, business rules, and database access.

| File | Responsibility |
| :--- | :--- |
| `main.py` | Application initialization, root route, and health endpoint |
| `controllers.py` | API routes and HTTP error responses |
| `services.py` | Business rules and deletion coordination |
| `repositories.py` | SQL queries and persistence |
| `schemas.py` | Request and response models |
| `clients.py` | HTTP communication with the Poll Service |
| `database.py` | MySQL connection configuration |
| `exceptions.py` | Application-specific exceptions |
| `sql/001_create_users.sql` | Initial database schema |
| `compose.yaml` | Container and network configuration |

The services maintain separate databases. Poll Service calls User Service to verify user registration; User Service calls Poll Service to clean up answers during deletion.

## Data Model

| Field | Description |
| :--- | :--- |
| `id` | Automatically generated primary key |
| `first_name` | First name, between 1 and 100 characters |
| `last_name` | Last name, between 1 and 100 characters |
| `email` | Email address stored as a string |
| `age` | Integer from 0 to 119 |
| `address` | Customer address |
| `joining_date` | Customer joining date, supplied with a timezone and normalized to UTC |
| `is_registered` | Registration flag; defaults to `false` |

Registration is performed through a dedicated endpoint. It is not a login or account authentication flow.

## Getting Started

### Prerequisites

- Docker with Docker Compose.
- Available local ports `8000` and `3307`.
- [Poll Service](https://github.com/noname1134/poll_service) running for successful deletion of existing users.

### 1. Clone the repository

```bash
git clone https://github.com/noname1134/user_service.git
cd user_service
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Replace the example database passwords in `.env`.

| Variable | Purpose |
| :--- | :--- |
| `MYSQL_DATABASE` | Database name |
| `MYSQL_USER` | Application database user |
| `MYSQL_PASSWORD` | Application database password |
| `MYSQL_ROOT_PASSWORD` | MySQL root password |
| `MYSQL_HOST` | Database host when running Python locally |
| `MYSQL_PORT` | Database port when running Python locally |
| `POLL_SERVICE_URL` | Poll Service URL when running Python locally |

Docker Compose configures the API to use `db:3306` for MySQL and `http://poll-api:8000` for the Poll Service. The database is exposed locally at `127.0.0.1:3307`.

Keep real credentials in `.env`; commit only placeholder values in `.env.example`.

### 3. Prepare the shared network

Create the external network if it does not already exist:

```bash
docker network create poll-system
```

Both services use this network. User Service joins with the alias `user-api`; Poll Service must join with the alias `poll-api` and listen on container port `8000`.

For user deletion, User Service calls:

```http
DELETE http://poll-api:8000/users/{user_id}/answers
```

### 4. Start the application

```bash
docker compose up --build -d
```

MySQL creates the table automatically when its database volume is first initialized. Start Poll Service using its own setup instructions to enable the complete polling workflow.

### 5. Explore the API

| Resource | URL |
| :--- | :--- |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI schema | http://localhost:8000/openapi.json |
| Health endpoint | http://localhost:8000/health |

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

The health endpoint checks API availability; it does not verify database or Poll Service connectivity.

### Useful commands

View API logs:

```bash
docker compose logs -f api
```

Stop the services:

```bash
docker compose down
```

The database volume persists after shutdown. SQL initialization scripts do not automatically reapply to an existing database volume.

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Retrieve the service greeting |
| `GET` | `/health` | Check API availability |
| `POST` | `/users` | Create a user |
| `GET` | `/users/{user_id}` | Retrieve a user |
| `PATCH` | `/users/{user_id}` | Partially update a user |
| `POST` | `/users/{user_id}/register` | Set registration status to `true` |
| `DELETE` | `/users/{user_id}` | Remove poll answers, then delete the user |

## Example Workflow

### Create a user

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Alex",
    "last_name": "Cohen",
    "email": "alex@example.com",
    "age": 25,
    "address": "Tel Aviv, Israel",
    "joining_date": "2026-11-02T10:00:00+02:00"
  }'
```

The new user has `is_registered: false`. The joining date in this example is normalized to `2026-11-02T08:00:00Z` in the response.

Use the returned user ID in subsequent requests. The examples below assume it is `1`.

### Register the user

```bash
curl -X POST http://localhost:8000/users/1/register
```

The response contains the updated user with `is_registered: true`.

### Update a profile field

```bash
curl -X PATCH http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"address": "Ramat Gan, Israel"}'
```

Omitted fields retain their existing values. Explicit `null` values are rejected.

### Retrieve the user

```bash
curl http://localhost:8000/users/1
```

### Delete the user

With Poll Service running:

```bash
curl -X DELETE http://localhost:8000/users/1
```

Expected response:

```json
{
  "message": "User deleted"
}
```

## Deletion Behavior

1. Check that the user exists.
2. Ask Poll Service to delete all answers belonging to the user.
3. Delete the profile from the User Service database.

If the Poll Service request fails or returns an unsuccessful HTTP status, the API responds with `503` and does not proceed to delete the user profile.

These operations are sequential HTTP and database operations, not a distributed transaction. If answer cleanup succeeds but profile deletion fails, the profile can remain after its answers have been removed.

## Error Handling

| HTTP Status | Example |
| :--- | :--- |
| `404 Not Found` | User does not exist |
| `422 Unprocessable Entity` | Invalid age, invalid name length, missing timezone, or explicit null in a profile update |
| `503 Service Unavailable` | Poll Service cannot be reached or returns an unsuccessful HTTP status during deletion |

## Testing and Code Quality

Run the following commands from the repository root using Python 3.10 or newer.

### Install development dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

### API tests

```bash
python -m pytest tests/test_users.py -v
```

The 12 API test cases exercise real FastAPI routes, request validation, and service logic while mocking database access and Poll Service calls. No running database or Poll Service is required.

Coverage includes user creation responses, invalid input, missing users, registration, deletion order, explicit null updates, and returning `503` without deleting the user when Poll Service cleanup fails.

### MySQL integration tests

Start the disposable MySQL 8.4 database, then enable the integration tests:

```bash
docker compose -p user-integration -f compose.test.yaml up -d --wait --wait-timeout 180
RUN_MYSQL_TESTS=1 python -m pytest tests/integration/ -v
```

The four integration tests execute real repository queries and verify:

- User fields are persisted with registration disabled by default.
- Timezone-aware joining dates are stored in UTC and returned with UTC timezone information.
- Registration updates persist across database connections.
- Deleting a user removes that record while preserving another user's record.

The test database uses port `3310`, dedicated test credentials, and temporary storage. It initializes from the existing `sql/` scripts. Each test cleans up its own records; stopping the container discards the temporary database.

Stop the test database when finished:

```bash
docker compose -p user-integration -f compose.test.yaml down
```

On Linux, prefix the Docker commands with `sudo` if your user lacks Docker socket access. Run Python commands from your activated virtual environment without `sudo`.

To run all 16 test cases with the test database running:

```bash
RUN_MYSQL_TESTS=1 python -m pytest tests/ -v
```

Without `RUN_MYSQL_TESTS=1`, the four database tests are skipped.

### Lint and formatting

```bash
ruff check .
ruff format --check .
```

Apply formatting locally with `ruff format .`.

### Continuous integration

[Python CI](https://github.com/noname1134/user_service/actions/workflows/ci.yml) runs automatically on pushes and pull requests:

| Job | Checks |
| :--- | :--- |
| `checks` | Ruff lint, formatting, and the API test suite; database tests are skipped |
| `mysql-integration` | Starts the temporary MySQL database and runs all four database integration tests |

The workflow uses Python 3.10 and stops the test database after the integration job, including when tests fail.

## Current Limitations

- Authentication and authorization are not implemented.
- Email addresses are stored as strings without email-format validation or a uniqueness constraint.
- Cross-service deletion is not atomic.
- SQL scripts initialize a new database; schema migrations are not implemented.
