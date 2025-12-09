#!/bin/sh
# Force all output to the enclave console
# Run app in foreground, redirecting to file.
# If it crashes, we proceed to tail the log so we can see what happened.
python3.11 -u /app/app.py >/tmp/enclave.log 2>&1

# If python exits, dump the log and keep the enclave alive for a bit to allow extraction
echo "[ENCLAVE] App exited. Dumping logs..." > /dev/console
cat /tmp/enclave.log > /dev/console
tail -f /tmp/enclave.log > /dev/console

echo "[ENCLAVE] Starting..."
echo "[ENCLAVE] Environment: $(uname -a)"

# Export unbuffered python
export PYTHONUNBUFFERED=1

# Run Python app
# Use exec to ensure signals are passed to the python process
# Run the application with unbuffered output
exec python3.11 -u /app/app.py
