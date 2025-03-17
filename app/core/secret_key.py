import os
import secrets

def generate_secret_key(dotenv_path: str) -> str:
    """
    set SECRET_KEY for current session if not set in .env file
    saves new key into .env
    """
    secret_key = os.getenv("SECRET_KEY")

    if not secret_key:
        secret_key = secrets.token_hex(32)

        try:
            with open(dotenv_path, "a") as f:
                f.write(f"SECRET_KEY={secret_key}\n")
            os.environ["SECRET_KEY"] = secret_key

        except Exception as e:
            print(f"Could not save SECRET_KEY to {dotenv_path}: {e}")
            os.environ["SECRET_KEY"] = secret_key

    return secret_key