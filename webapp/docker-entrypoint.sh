#!/bin/bash
set -e

export PATH=/root/.local/bin/:$PATH

wait_for_db() {
    echo " ++ Waiting for database to be ready..."
    
    # Check for PostgreSQL environment variables
    if [[ -n "$PG_HOST" && -n "$PG_DB" && -n "$PG_USER" ]]; then
        echo " +++ Detected PostgreSQL configuration"
        echo " +++ PG_HOST: $PG_HOST"
        echo " +++ PG_DB: $PG_DB"
        echo " +++ PG_USER: $PG_USER"
        echo " +++ PostgreSQL connection configured!"
    else
        echo " --- PostgreSQL environment variables not set:"
        echo " --- PG_HOST: ${PG_HOST:-NOT_SET}"
        echo " --- PG_DB: ${PG_DB:-NOT_SET}"
        echo " --- PG_USER: ${PG_USER:-NOT_SET}"
        echo " --- This may cause Django to use default database configuration"
    fi
}

# If first argument is the webapp, start the server
if [ "$1" = "webapp" ]; then
    echo " ++ Starting Beryl3 Django Application"
    wait_for_db
    echo " ++ Starting Gunicorn server..."
    exec uv run gunicorn webapp.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 1 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        --log-level info
else
    # For jobs and other commands, just execute them directly
    exec "$@"
fi