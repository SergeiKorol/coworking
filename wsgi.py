"""WSGI entry point for production hosts (PythonAnywhere, HelioHost)."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from app import create_app

app = create_app()
