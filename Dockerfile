FROM python:3.12-slim

# Ställ in arbetskatalogen i containern
WORKDIR /app

# Kopiera över requirements.txt till containern
COPY requirements.txt .

# Installera alla Python-paket som anges i requirements.txt
RUN pip install -r requirements.txt

# Kopiera över hela appen till containern
COPY . .

# Kör Gunicorn med rätt bindning
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]