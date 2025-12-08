import socket
import sys

def main():
    cid = 16
    port = 5000
    print(f"Connecting to Enclave CID {cid} Port {port}...", flush=True)
    
    try:
        # Create vsock socket (AF_VSOCK usually 40)
        sock = socket.socket(40, socket.SOCK_STREAM)
    except Exception as e:
        print(f"Failed to create socket: {e}")
        # Try finding constant dynamically
        try:
            sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        except:
            print("Could not create vsock socket. Ensure kernel module loaded.")
            return

    try:
        sock.settimeout(5)
        sock.connect((cid, port))
        print("Connected!", flush=True)
        
        data = sock.recv(1024)
        print(f"Received greeting: {data}", flush=True)
        
        sock.sendall(b"Hello Enclave")
        response = sock.recv(1024)
        print(f"Received echo: {response}", flush=True)
        
        sock.close()
        print("Success!", flush=True)
    except Exception as e:
        print(f"Connection failed: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
