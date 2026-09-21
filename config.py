import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave_secreta_provisoria')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///portal_canhotos.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Credenciais Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'SUA_URL_DO_SUPABASE')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'SUA_KEY_DO_SUPABASE')
    SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'canhotos')
