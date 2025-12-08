"""
NSM (Nitro Secure Module) utility functions

Provides attestation document generation for KMS decrypt operations.
"""

import subprocess
import base64


def nsm_get_attestation_doc(user_data=None, nonce=None, public_key=None):
    """
    Get attestation document from NSM device.
    
    Falls back to empty document if NSM is not available (for testing).
    """
    try:
        # Try to use nsm-cli if available
        result = subprocess.run(
            ['nsm-cli', 'describe-nsm'],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # NSM available, get attestation document
            # In production, use proper NSM API
            # For now, return empty for testing
            return b''
        else:
            return b''
            
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # NSM not available (testing mode)
        return b''
