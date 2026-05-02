from dotenv import load_dotenv

load_dotenv()

from backend.app import create_app

app = create_app()
