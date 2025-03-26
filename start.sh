#!/bin/bash

cd "$(dirname "$0")"

mkdir -p logs

export FLASK_APP=app.py
export FLASK_ENV=development

if [ -f .env ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ ! "$line" =~ ^#.*$ ]] && [ -n "$line" ]; then
            export "$line"
        fi
    done < .env
fi

if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:5010 \
    --workers 3 \
    --worker-class sync \
    --threads 4 \
    --timeout 300 \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    --reload \
    app:app