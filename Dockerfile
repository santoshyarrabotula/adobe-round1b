FROM python:3.11-slim

WORKDIR /app

# System dependencies for PyMuPDF and fonts
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Add preloaded NLTK data
COPY nltk_data /root/nltk_data

# Download model weights in advance
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy main code
COPY main.py ./
COPY app ./app

# Run
CMD ["python", "main.py"]
