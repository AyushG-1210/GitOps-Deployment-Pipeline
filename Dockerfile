# Use an official lightweight Python image
FROM python:3.13-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first to leverage Docker's layer caching
COPY requirements.txt .

# Install Python packages (CPU-only torch, see requirements.txt)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the server script, frontend and trained weights into the container
COPY . .

# Create a non-root user and set ownership of the app directory
RUN groupadd --system appgroup && useradd --system --gid appgroup --create-home appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Defaults; hosting platforms (Render, Cloud Run, ...) override PORT.
# Each worker loads its own copy of torch (~300 MB), so keep this low on small plans.
ENV PORT=8000 \
    WEB_CONCURRENCY=1

EXPOSE 8000

# Shell form so ${PORT} is expanded at runtime; exec so uvicorn receives signals
CMD exec uvicorn server:app --host 0.0.0.0 --port ${PORT} --workers ${WEB_CONCURRENCY}
