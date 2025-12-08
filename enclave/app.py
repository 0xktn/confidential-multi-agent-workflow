"""
Minimal VSOCK Echo Server
Uses only standard library (socket) to test enclave connectivity.
No boto3/cryptography needed.
"""

import socket
import sys
import time

def main():
    print("VSOCK Server Starting...", flush=True)
    
    # Create vsock socket
    try:
        # AF_VSOCK = 40 on Linux/Python 3.7+ if available
        # On some older python versions or non-linux, it might not be defined
        # But we are in Alpine/Linux.
        sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    except AttributeError:
        # Fallback manual constant if python < 3.7 or missing link
        sock = socket.socket(40, socket.SOCK_STREAM)
        
    cid = socket.VMADDR_CID_ANY
    port = 5000
    
    print(f"Binding to CID: {cid}, Port: {port}", flush=True)
    sock.bind((cid, port))
    sock.listen(1) # Listen for 1 connection
    
    print(f"Listening on port {port}...", flush=True)
    
    while True:
        try:
            conn, addr = sock.accept()
            print(f"Connection from: {addr}", flush=True)
            
            # Send greeting
            conn.sendall(b"HELLO FROM ENCLAVE\n")
            
            # Echo loop
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Received: {data}", flush=True)
                conn.sendall(data)
                
            conn.close()
            print("Connection closed", flush=True)
            
        except Exception as e:
            print(f"Error handling connection: {e}", flush=True)
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}", flush=True)
        # Keep alive to see error in potential logs
        while True:
            time.sleep(60)
