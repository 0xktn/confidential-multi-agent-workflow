"""
Temporal Activities

Activities that communicate with the enclave via vsock.
"""

import socket
import json
import logging
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def process_in_enclave(request_data: str) -> str:
    """
    Send data to enclave for confidential processing via vsock.
    
    Returns encrypted blob as JSON string.
    """
    logger.info(f"Sending to enclave: {request_data[:50]}...")
    
    try:
        # Connect to enclave on CID 16, port 5000
        sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        sock.connect((16, 5000))
        
        # Send request
        request = {'data': request_data}
        sock.sendall(json.dumps(request).encode())
        
        # Receive encrypted response
        response_data = sock.recv(4096)
        encrypted_result = json.loads(response_data.decode())
        
        sock.close()
        
        logger.info("Received encrypted result from enclave")
        
        # Return encrypted blob as JSON string
        # This will be stored in Temporal history as ciphertext
        return json.dumps(encrypted_result)
        
    except Exception as e:
        logger.error(f"Failed to communicate with enclave: {e}")
        raise
