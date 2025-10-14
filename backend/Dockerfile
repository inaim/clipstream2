FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including build tools for bcrypt
RUN apt-get update && apt-get install -y \
    ffmpeg curl wget \
    gcc g++ make \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p uploads logs

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
