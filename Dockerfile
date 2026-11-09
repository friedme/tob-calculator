# Base image pinned by digest (Python 3.11.18, Debian trixie) so rebuilds are reproducible.
# Bump it deliberately: see "Dependencies" in CLAUDE.md.
FROM python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535
WORKDIR /app
COPY requirements.txt .
# requirements.txt is a full lock; --no-deps + pip check fail the build if it is incomplete
RUN pip install --no-cache-dir --no-deps -r requirements.txt && pip check
COPY . .
RUN mkdir -p uploads outputs
EXPOSE 5000
CMD ["python", "app.py"]
