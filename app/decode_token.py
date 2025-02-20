import jwt
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

token = "YOUR_VALID_TOKEN_HERE"
secret_key = os.getenv("SECRET_KEY")

try:
    decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
    print("Decoded Token:", decoded)
except jwt.ExpiredSignatureError:
    print("Token has expired!")
except jwt.InvalidTokenError:
    print("Invalid Token!")
