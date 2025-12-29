FROM public.ecr.aws/docker/library/python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

# Install dependencies
# Upgrade pip to avoid warnings and ensure best compatibility
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

# Start the server with gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
