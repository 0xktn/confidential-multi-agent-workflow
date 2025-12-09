# Debug: Prove console write works immediately
echo "[ENCLAVE] BOOTING..." > /dev/console

# Setup log file and background streamer
touch /tmp/enclave.log
tail -f /tmp/enclave.log > /dev/console &
TAIL_PID=$!

echo "[ENCLAVE] STARTING PYTHON..." >> /tmp/enclave.log
which python3.11 >> /tmp/enclave.log 2>&1

# Run app
python3.11 -u /app/app.py >> /tmp/enclave.log 2>&1

# Cleanup
kill $TAIL_PID

echo "[ENCLAVE] Starting..."
echo "[ENCLAVE] Environment: $(uname -a)"

# Export unbuffered python
export PYTHONUNBUFFERED=1

# Run Python app
# Use exec to ensure signals are passed to the python process
# Run the application with unbuffered output
exec python3.11 -u /app/app.py
