import os
import sys

# Ensure the app module can be imported from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Export the Flask WSGI app for Vercel.
__all__ = ['app']
