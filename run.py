import os
import sys
from flask import Flask
from dotenv import load_dotenv
from app import db, create_app

print("Current Working Directory:", os.getcwd())
print("Python Path:", sys.path)

load_dotenv()

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
