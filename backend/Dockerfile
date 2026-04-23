FROM python:3.11-slim

WORKDIR /app

# libmagic1 → python-magic; exiftool → PyExifTool subprocess wrapper
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    exiftool \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# --reload watches for code changes when the source is volume-mounted
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--reload", "wsgi:app"]
