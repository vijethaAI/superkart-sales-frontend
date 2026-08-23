FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 7860

# BACKEND_URL is overridden at runtime via a Space "Variable" once the
# backend Space is deployed (see the deployment guide).
ENV BACKEND_URL="http://127.0.0.1:7860"

CMD streamlit run app.py --server.port=${PORT:-7860} --server.address=0.0.0.0
