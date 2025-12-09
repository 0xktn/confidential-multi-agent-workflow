import socket
import json
import sys

# Standard AWS Sample Logic (Isolated)
def run_server():
    cid = socket.VMADDR_CID_ANY
    port = 5000
    
    print(f"[ISOLATED] Starting on CID {cid} Port {port}", flush=True)
    
    s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    s.bind((cid, port))
    s.listen(5)
    
    while True:
        try:
            conn, addr = s.accept()
            print(f"[ISOLATED] Connection from {addr}", flush=True)
            
            data = conn.recv(1024)
            if not data:
                conn.close()
                continue
                
            print(f"[ISOLATED] Recv {len(data)} bytes", flush=True)
            
            # CRASH TEST 1: DECODE
            try:
                msg = data.decode('utf-8')
                print(f"[ISOLATED] Decoded: {msg}", flush=True)
            except Exception as e:
                print(f"[ISOLATED] DOS Decode Fail: {e}", flush=True)
                conn.close()
                continue

            # CRASH TEST 2: JSON
            try:
                obj = json.loads(msg)
                print(f"[ISOLATED] JSON parsed: {obj}", flush=True)
                resp = json.dumps({"status": "ok", "echo": obj})
                conn.sendall(resp.encode('utf-8'))
            except Exception as e:
                print(f"[ISOLATED] JSON Fail: {e}", flush=True)
                conn.sendall(b'{"status": "error"}')

            conn.close()
        except Exception as e:
            print(f"[ISOLATED] Loop Error: {e}", flush=True)

if __name__ == "__main__":
    run_server()
