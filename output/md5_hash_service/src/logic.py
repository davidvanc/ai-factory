import hashlib

def calculate_md5(text: str) -> str:
    """
    Berekent de MD5 hash van de meegegeven string en retourneert deze als hexadecimale waarde.
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()
