#!/bin/sh

# Setup log file
touch /tmp/enclave.log

# Background broadcaster: Spams console with state every 2s so we can't miss it
(
  while true; do
    echo "=== [$(date)] ENCLAVE MONITOR ===" > /dev/console
    echo "--- PROCESSES ---" > /dev/console
    ps -ef > /dev/console
    echo "--- LOG TAIL (20 lines) ---" > /dev/console
    tail -n 20 /tmp/enclave.log > /dev/console
    sleep 2
  done
) &

echo "[ENCLAVE] STARTING PYTHON..." >> /tmp/enclave.log
python3.11 -u /app/app.py >> /tmp/enclave.log 2>&1
echo "[ENCLAVE] PYTHON EXITED WITH CODE $?" >> /tmp/enclave.log

# Keep alive to continue broadcasting logs
tail -f /tmp/enclave.log > /dev/console

echo "[ENCLAVE] Starting..."
echo "[ENCLAVE] Environment: $(uname -a)"

# Export unbuffered python
export PYTHONUNBUFFERED=1

# Run Python app
# Use exec to ensure signals are passed to the python process
# Run the application with unbuffered output
exec python3.11 -u /app/app.py
