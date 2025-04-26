# Dockerfile

# 1. Velg base-image (liten python image)
FROM python:3.11-slim

# 2. Sett working directory
WORKDIR /app

# 3. Kopier requirements.txt og installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Kopier hele prosjektet
COPY . .

# 5. Sett environment variables
ENV PYTHONUNBUFFERED=1

# 6. Eksponer port 8000 (standard FastAPI port)
EXPOSE 8000

# 7. Start FastAPI app med uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
