
def str2bytes(maybe_str):
    if not isinstance(maybe_str,bytes) and isinstance(maybe_str,str):
        maybe_str = maybe_str.encode()
    return maybe_str

def bytes2str(maybe_bytes):
    if isinstance(maybe_bytes,bytes) and not isinstance(maybe_bytes,str):
        maybe_bytes = maybe_bytes.decode()
    return maybe_bytes
