FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY app.py .

# Expose Streamlit's default port
EXPOSE 8501

# Healthcheck ensures the container is responsive
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
ENTRYPOINT ["/usr/local/bin/streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]