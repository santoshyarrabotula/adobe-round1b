FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF and text extraction
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Download required NLTK data
RUN python -m nltk.downloader -d /root/nltk_data punkt

# Copy the application code
COPY main.py ./
COPY app ./app

# Run the app
CMD ["python", "main.py"]
