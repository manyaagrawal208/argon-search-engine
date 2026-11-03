# Container image for hosts that run Docker (e.g. Hugging Face Spaces).
FROM python:3.11-slim

# Hugging Face Spaces runs containers as UID 1000
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY --chown=user . .

EXPOSE 7860
# GROQ_API_KEY is supplied by the host as a secret / environment variable
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--timeout", "60", "app:app"]
