# ui/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install only what the UI needs
COPY ui/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit app
COPY ui/ .

# Expose Streamlit port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
