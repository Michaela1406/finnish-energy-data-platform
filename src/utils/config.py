import os

def get_api_key() -> str:
    
    api_key = os.getenv("FINGRID_API_KEY")
    
    if not api_key:
        raise RuntimeError("FINGRID_API_KEY environment variable is not set")
    
    return api_key
