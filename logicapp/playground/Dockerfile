FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY playground.py .

EXPOSE 8501
# Bind to all interfaces and disable CORS/XSRF so Streamlit's websocket works behind the ACA ingress proxy.
CMD ["streamlit", "run", "playground.py", \
     "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", \
     "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
