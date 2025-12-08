"""
Enclave Application Entry Point

Implements confidential processing with KMS attestation and AES-256-GCM encryption.
"""

import os
import sys
import json
import socket
import base64
import logging
from typing import Dict, Any

import boto3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KMSAttestationClient:
    """Handles KMS attestation and TSK decryption"""
    
    def __init__(self, kms_key_id: str, encrypted_tsk_b64: str, region: str = 'ap-southeast-1'):
        self.kms_key_id = kms_key_id
        self.encrypted_tsk = base64.b64decode(encrypted_tsk_b64)
        self.region = region
        self.tsk = None
        
    def get_attestation_document(self) -> bytes:
        """Generate attestation document from NSM device"""
        try:
            # Open NSM device
            with open('/dev/nsm', 'rb') as nsm:
                # Request attestation document
                # Format: https://github.com/aws/aws-nitro-enclaves-nsm-api
                request = {
                    'Attestation': {
                        'user_data': None,
                        'nonce': None,
                        'public_key': None
                    }
                }
                
                # Write request (simplified - actual NSM uses CBOR)
                # For now, use aws-nsm-interface library
                from nsm_util import nsm_get_attestation_doc
                doc = nsm_get_attestation_doc()
                return doc
        except Exception as e:
            logger.error(f"Failed to get attestation document: {e}")
            # Fallback: return empty bytes for testing without NSM
            logger.warning("Using empty attestation document (testing mode)")
            return b''
        
    def decrypt_tsk(self) -> bytes:
        """Request TSK from KMS with attestation"""
        logger.info("Requesting TSK from KMS with attestation...")
        
        try:
            client = boto3.client('kms', region_name=self.region)
            
            attestation_doc = self.get_attestation_document()
            
            if attestation_doc:
                # Production: decrypt with attestation
                response = client.decrypt(
                    CiphertextBlob=self.encrypted_tsk,
                    Recipient={
                        'KeyEncryptionAlgorithm': 'RSAES_OAEP_SHA_256',
                        'AttestationDocument': attestation_doc
                    }
                )
                self.tsk = response['Plaintext']
                logger.info("TSK decrypted successfully with attestation")
            else:
                # Fallback: decrypt without attestation (testing)
                logger.warning("Decrypting TSK without attestation (testing mode)")
                response = client.decrypt(CiphertextBlob=self.encrypted_tsk)
                self.tsk = response['Plaintext']
                
            return self.tsk
            
        except Exception as e:
            logger.error(f"Failed to decrypt TSK: {e}")
            raise


class EncryptionService:
    """Handles AES-256-GCM encryption/decryption"""
    
    def __init__(self, tsk: bytes):
        self.aesgcm = AESGCM(tsk)
        logger.info("Encryption service initialized")
        
    def encrypt(self, plaintext: bytes) -> Dict[str, str]:
        """Encrypt with AES-256-GCM"""
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, None)
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'nonce': base64.b64encode(nonce).decode()
        }
        
    def decrypt(self, encrypted_data: Dict[str, str]) -> bytes:
        """Decrypt with AES-256-GCM"""
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        nonce = base64.b64decode(encrypted_data['nonce'])
        
        return self.aesgcm.decrypt(nonce, ciphertext, None)


class VsockServer:
    """vsock server for host communication"""
    
    def __init__(self, encryption_service: EncryptionService, port: int = 5000):
        self.port = port
        self.encryption_service = encryption_service
        
    def start(self):
        """Listen on vsock"""
        logger.info(f"Starting vsock server on port {self.port}...")
        
        sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        sock.bind((socket.VMADDR_CID_ANY, self.port))
        sock.listen()
        
        logger.info("vsock server listening, waiting for connections...")
        
        while True:
            try:
                conn, addr = sock.accept()
                logger.info(f"Connection from {addr}")
                self.handle_request(conn)
            except Exception as e:
                logger.error(f"Error handling connection: {e}")
                
    def handle_request(self, conn: socket.socket):
        """Process request from host"""
        try:
            # Receive request
            data = conn.recv(4096)
            if not data:
                logger.warning("Empty request received")
                conn.close()
                return
                
            request = json.loads(data.decode())
            logger.info(f"Received request: {request.get('data', '')[:50]}...")
            
            # Process data (placeholder - add actual logic here)
            input_data = request.get('data', '')
            result = f"Processed: {input_data}"
            
            # Encrypt result
            encrypted = self.encryption_service.encrypt(result.encode())
            logger.info("Result encrypted successfully")
            
            # Send response
            response = json.dumps(encrypted)
            conn.sendall(response.encode())
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            error_response = json.dumps({'error': str(e)})
            conn.sendall(error_response.encode())
        finally:
            conn.close()


def main():
    """Main entry point"""
    logger.info("Starting enclave application...")
    
    # Get configuration from environment
    kms_key_id = os.environ.get('KMS_KEY_ID')
    encrypted_tsk_b64 = os.environ.get('ENCRYPTED_TSK')
    region = os.environ.get('AWS_REGION', 'ap-southeast-1')
    
    if not kms_key_id or not encrypted_tsk_b64:
        logger.error("Missing required environment variables: KMS_KEY_ID, ENCRYPTED_TSK")
        sys.exit(1)
    
    try:
        # Initialize KMS client and decrypt TSK
        kms_client = KMSAttestationClient(kms_key_id, encrypted_tsk_b64, region)
        tsk = kms_client.decrypt_tsk()
        
        # Initialize encryption service
        encryption_service = EncryptionService(tsk)
        
        # Start vsock server
        server = VsockServer(encryption_service)
        server.start()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
