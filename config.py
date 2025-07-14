import os;
from dotenv import load_dotenv;

load_dotenv()

class Config:
    LICHESS_API_URL = 'https://lichess.org/api'
    LICHESS_TOKEN = os.getenv('LICHESS_TOKEN', '')