# api/index.py
from .api import app

# Vercel serverless handler
handler = app
