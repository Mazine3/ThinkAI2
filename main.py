from app import app
import os
from dotenv import load_dotenv

load_dotenv()

PORT = os.getenv('PORT','')
DEBUG = os.getenv('DEBUG', '')

if __name__ == "__main__":
    app.run(debug=DEBUG, port=PORT)