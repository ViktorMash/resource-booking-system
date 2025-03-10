# Resource Booking System

A web application for booking various resources (computational resources, meeting rooms, equipment, etc.) with user permissions management

## Technology Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT Tokens
- **Containerization**: Docker and Docker Compose

### Prerequisites

- Git
- Docker
- Docker Compose

### Installation Steps

#### 1. Clone the repository

```bash
git clone <repository-url>
cd resource-booking-system
```

#### 2. Configure environment variables

Check and edit the `docker/.env` file if necessary:

Make sure the following parameters are configured correctly:
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `DB_PORT`
- `DB_SERVER`
- `SECRET_KEY` (for JWT tokens)

#### 3. Start the database

```bash
cd docker
docker compose up -d db
```

#### 4. Managing Migrations

The application uses Alembic for database migrations.
When you make changes to database models, you need to create a new migration:

```bash
# go to root folder
cd..

# Apply the migration
alembic upgrade head
```
After applying migrations, the database schema will be ready for use with all required tables

#### 5.Build and start the application

```bash
cd docker
docker compose up -d app
```


6.**Verify application**

After successful startup, the API will be available at:
- API Documentation: http://localhost:8000


## Troubleshooting

### Database Connection Issues

If the application can't connect to the database:

1. Check if PostgreSQL container is running:
```bash
docker ps | grep postgres
```

2. Verify database credentials in `.env`

3. Check PostgreSQL logs:
```bash
docker ps
docker logs <db-container-name>
```

### Docker Errors

If containers fail to start:

1. Check Docker logs:
```bash
docker compose logs
```

2. Ensure ports are not already in use:
```bash
lsof -i :8000
lsof -i :5432
```

3. Try rebuilding the containers:
```bash
docker compose down
docker compose up -d
```