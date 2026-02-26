#!/bin/sh
set -e

echo "===================="
echo "Starting SDG Assessment Application"
echo "Environment: ${FLASK_ENV:-development}"
echo "===================="

# Wait for database to be ready
echo "Waiting for database..."
until nc -z "${DB_HOST:-db}" "${DB_PORT:-5432}" 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 1
done
echo "Database is up!"

# Run migrations with timeout
echo "Running database migrations..."
timeout 60 flask db upgrade || {
    echo "Migration failed or timed out"
    exit 1
}

echo "Migrations complete!"

# Start server with appropriate configuration based on environment
echo "Starting Gunicorn server..."
if [ "$FLASK_ENV" = "production" ]; then
    echo "Using production configuration (gunicorn_config.prod.py)"
    exec gunicorn --config gunicorn_config.prod.py run:app
else
    echo "Using development configuration (gunicorn_config.py)"
    exec gunicorn --config gunicorn_config.py run:app
fi
