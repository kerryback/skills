# Voiceover Builder — container image.
# Multi-stage: build the React SPA, then a Python runtime with quarto.
# NOTE: quarto (deck render) is the one heavy dependency. PowerPoint support was
# dropped — teachers export decks to PDF — so LibreOffice is no longer bundled.

# ---- Stage 1: build the frontend ----
FROM node:22-slim AS frontend
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build          # -> /fe/dist

# ---- Stage 2: python runtime ----
FROM python:3.12-slim

ARG QUARTO_VERSION=1.6.43
ENV DEBIAN_FRONTEND=noninteractive \
    DATA_DIR=/data

# quarto (deck render), plus curl/ca-certs. ffmpeg for video render comes from
# the imageio-ffmpeg pip wheel (bundled static binary), so it is not apt-installed.
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates \
    && curl -sL "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.deb" -o /tmp/quarto.deb \
    && dpkg -i /tmp/quarto.deb && rm /tmp/quarto.deb \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code
COPY backend/ ./backend/
COPY runtime-template/ ./runtime-template/
COPY --from=frontend /fe/dist ./frontend/dist

# Persistent project data (mount a volume here in production)
VOLUME ["/data"]

# The app needs, at runtime (set as env, never baked in):
#   ELEVENLABS_API_KEY  (TTS; the only key — narration comes from Claude Code)
ENV PORT=8000
WORKDIR /app/backend
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
