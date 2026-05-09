# config.py

import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # MySQL Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'password')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'dream_simulator')
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # AI Configuration (for dream generation)
    AI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    AI_MODEL = 'gpt-4'
    
    # Dream Engine Settings
    MAX_FEAR_LEVEL = 10.0
    FEAR_DECAY_RATE = 0.05
    TENSION_BUILD_RATE = 0.1
    NIGHTMARE_THRESHOLD = 7.5
    
    # Psychological depth levels
    DEPTH_LEVELS = {
        1: "Surface Dreams",
        2: "Subconscious Echoes", 
        3: "Deep Memory",
        4: "Primal Fears",
        5: "The Void"
    }
