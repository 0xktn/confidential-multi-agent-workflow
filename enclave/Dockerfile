FROM python:3.11-alpine

WORKDIR /app

# Install simple dependencies just for test
# RUN pip install cryptography boto3

# Explicitly redirect to console device to ensure logs are visible
CMD ["/bin/sh", "-c", "exec >/dev/console 2>&1; echo 'REDIRECTED CONSOLE START'; python3 -u /app/app.py"]
