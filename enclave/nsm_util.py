import ctypes
import base64
import os

# Define Structs
class NsmAttestationDocRequest(ctypes.Structure):
    _fields_ = [
        ("public_key", ctypes.POINTER(ctypes.c_ubyte)),
        ("public_key_len", ctypes.c_uint32),
        ("nonce", ctypes.POINTER(ctypes.c_ubyte)),
        ("nonce_len", ctypes.c_uint32),
        ("user_data", ctypes.POINTER(ctypes.c_ubyte)),
        ("user_data_len", ctypes.c_uint32),
    ]

def get_attestation_doc_b64():
    """
    Get the attestation document from the NSM and return it as a base64 string.
    Returns: (base64_string, error_message)
    """
    
    # 1. Locate Library
    lib_path = None
    if os.path.exists("libnsm.so"):
        lib_path = os.path.abspath("libnsm.so")
    elif os.path.exists("/usr/lib64/libnsm.so"):
        lib_path = "/usr/lib64/libnsm.so"
    else:
        return None, "libnsm.so not found in /app or /usr/lib64"

    # 2. Load Library
    try:
        libnsm = ctypes.CDLL(lib_path)
    except Exception as e:
        return None, f"Failed to load {lib_path}: {e}"

    # 3. Define Signatures
    try:
        libnsm.nsm_lib_init.restype = ctypes.c_int
        libnsm.nsm_lib_init.argtypes = []
        
        libnsm.nsm_lib_exit.restype = ctypes.c_int
        libnsm.nsm_lib_exit.argtypes = []
        
        libnsm.nsm_fd_open.restype = ctypes.c_int
        libnsm.nsm_fd_open.argtypes = []
        
        libnsm.nsm_fd_close.restype = None
        libnsm.nsm_fd_close.argtypes = [ctypes.c_int]
        
        libnsm.nsm_get_attestation_doc.restype = ctypes.c_int
        libnsm.nsm_get_attestation_doc.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(NsmAttestationDocRequest),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_uint32)
        ]
    except Exception as e:
         return None, f"Failed to define signatures: {e}"

    # 4. Use Library
    # Initialize
    if libnsm.nsm_lib_init() != 0:
        return None, "nsm_lib_init failed"

    fd = libnsm.nsm_fd_open()
    if fd < 0:
        libnsm.nsm_lib_exit()
        return None, "nsm_fd_open failed (check /dev/nsm permissions)"

    try:
        # Prepare empty request
        req = NsmAttestationDocRequest()
        req.public_key = None
        req.public_key_len = 0
        req.nonce = None
        req.nonce_len = 0
        req.user_data = None
        req.user_data_len = 0
        
        # Buffer (16KB)
        buf_len = 16 * 1024
        buf = (ctypes.c_ubyte * buf_len)()
        out_len = ctypes.c_uint32(buf_len)
        
        res = libnsm.nsm_get_attestation_doc(
            fd, 
            ctypes.byref(req), 
            ctypes.sizeof(req), 
            buf, 
            ctypes.byref(out_len)
        )
        
        if res != 0:
             return None, f"nsm_get_attestation_doc failed with code {res}"
            
        doc_bytes = bytes(buf[:out_len.value])
        return base64.b64encode(doc_bytes).decode('utf-8'), None

    except Exception as e:
        return None, f"Runtime error: {e}"
    finally:
        libnsm.nsm_fd_close(fd)
        libnsm.nsm_lib_exit()
