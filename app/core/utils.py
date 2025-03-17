from fastapi import status

def get_status_suffix(status_code):
    for name, value in vars(status).items():
        if value == status_code and name.startswith('HTTP_'):
            return name.split("_", 2)[2].capitalize().replace("_", " ")