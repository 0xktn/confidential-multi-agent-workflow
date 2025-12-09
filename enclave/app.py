import socket
import sys
import os
import base64
import subprocess
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Force line buffering
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("[ENCLAVE] Manual Handler V2 (Functional) Starting...", flush=True)

# Global State
CREDENTIALS = {
    'ak': None,
    'sk': None,
    'token': None
}
ENCRYPTION_KEY = None # 32-byte TSK

def kms_decrypt(ciphertext_b64):
    print(f"[ENCLAVE] Decrypting blob len={len(ciphertext_b64)}", flush=True)
    try:
        cmd = [
            '/usr/bin/kmstool_enclave_cli', 'decrypt',
            '--region', 'ap-southeast-1',
            '--proxy-port', '8000',
            '--ciphertext', ciphertext_b64
        ]
        if CREDENTIALS['ak']:
            cmd.extend(['--aws-access-key-id', CREDENTIALS['ak']])
        if CREDENTIALS['sk']:
            cmd.extend(['--aws-secret-access-key', CREDENTIALS['sk']])
        if CREDENTIALS['token']:
            cmd.extend(['--aws-session-token', CREDENTIALS['token']])
        
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()
        if "PLAINTEXT:" in output:
            payload = output.split("PLAINTEXT:", 1)[1].strip()
            return base64.b64decode(payload)
        return base64.b64decode(output)
    except Exception as e:
        print(f"[ERROR] KMS Decrypt failed: {e}", flush=True)
        return None

def extract_val(msg_str, key):
    # Rudimentary JSON parser for specific keys
    if f'"{key}":' not in msg_str and f'"{key}":' not in msg_str: return None
    try:
        sub = msg_str.split(f'"{key}"')[1]
        # skip until colon
        sub = sub.split(':', 1)[1].strip()
        # skip quote
        if sub.startswith('"'):
            val = sub.split('"', 2)[1]
            return val
        return None
    except:
        return None

def run_server():
    cid = socket.VMADDR_CID_ANY
    port = 5000
    
    try:
        s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        s.bind((cid, port))
        s.listen(5)
        print(f"[ENCLAVE] Listening on CID {cid} Port {port}", flush=True)
    except Exception as e:
        print(f"[FATAL] Bind failed: {e}", flush=True)
        return

    while True:
        try:
            conn, addr = s.accept()
            print(f"[ENCLAVE] Connect from {addr}", flush=True)
            
            try:
                data = conn.recv(8192)
                if not data:
                    conn.close()
                    continue
                
                # Careful decode
                try:
                    msg_str = data.decode('utf-8', errors='ignore')
                except:
                    msg_str = ""
                
                print(f"[ENCLAVE] Recv {len(data)} bytes", flush=True)

                # HANDLER DISPATCH
                if '"type": "ping"' in msg_str or '"type":"ping"' in msg_str:
                    conn.sendall(b'{"status": "ok", "msg": "pong"}')
                
                elif '"type": "configure"' in msg_str or '"type":"configure"' in msg_str:
                    print("[ENCLAVE] Handling Configure", flush=True)
                    ak = extract_val(msg_str, "access_key_id")
                    sk = extract_val(msg_str, "secret_access_key")
                    token = extract_val(msg_str, "session_token")
                    enc_key = extract_val(msg_str, "encrypted_key")
                    
                    if ak and sk and token and enc_key:
                        CREDENTIALS['ak'] = ak
                        CREDENTIALS['sk'] = sk
                        CREDENTIALS['token'] = token
                        
                        tsk = kms_decrypt(enc_key)
                        if tsk and len(tsk) == 32:
                            global ENCRYPTION_KEY
                            ENCRYPTION_KEY = tsk
                            print("[ENCLAVE] Configuration Successful", flush=True)
                            conn.sendall(b'{"status": "ok", "msg": "configured"}')
                        else:
                            print("[ERROR] TSK decryption failed", flush=True)
                            conn.sendall(b'{"status": "error", "msg": "kms_fail"}')
                    else:
                        print(f"[ERROR] Missing fields in config", flush=True)
                        conn.sendall(b'{"status": "error", "msg": "missing_fields"}')

                elif '"type": "process"' in msg_str or '"type":"process"' in msg_str:
                    print("[ENCLAVE] Handling Process", flush=True)
                    if not ENCRYPTION_KEY:
                        conn.sendall(b'{"status": "error", "msg": "not_configured"}')
                    else:
                        enc_data_b64 = extract_val(msg_str, "encrypted_data")
                        if enc_data_b64:
                            try:
                                blob = base64.b64decode(enc_data_b64)
                                nonce = blob[:12]
                                ciphertext = blob[12:]
                                aesgcm = AESGCM(ENCRYPTION_KEY)
                                plaintext = aesgcm.decrypt(nonce, ciphertext, None)
                                
                                # Process logic: Just echo "Processed: <text>"
                                resp_text = f"Processed: {plaintext.decode('utf-8')}"
                                
                                # Encrypt response
                                resp_nonce = os.urandom(12)
                                resp_cipher = aesgcm.encrypt(resp_nonce, resp_text.encode(), None)
                                resp_blob = base64.b64encode(resp_nonce + resp_cipher).decode()
                                
                                conn.sendall(f'{{"status": "ok", "encrypted_data": "{resp_blob}"}}'.encode())
                            except Exception as e_proc:
                                print(f"[ERROR] Process logic error: {e_proc}", flush=True)
                                conn.sendall(b'{"status": "error", "msg": "process_fail"}')
                        else:
                             conn.sendall(b'{"status": "error", "msg": "missing_data"}')
                else:
                     conn.sendall(b'{"status": "error", "msg": "unknown_type"}')

            except Exception as e_req:
                print(f"[ERROR] Request failed: {e_req}", flush=True)
            finally:
                conn.close()
        except Exception as e_acc:
             print(f"[FATAL] Accept failed: {e_acc}", flush=True)

if __name__ == "__main__":
    run_server()
