"""WSGI entry point for production hosts (PythonAnywhere, HelioHost)."""

from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()
