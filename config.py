import os

class Config:
    """Base config."""
    PRCORE_HEADERS = {'Authorization':'Bearer UaJW0QvkMA1cVnOXB89E0NbLf3JRRoHwv2wWmaY5v=QYpaxr1UD9/FupeZ85sa2r'}
    PRCORE_BASE_URL = 'https://prcore.chaos.run'
    MONGO_URI = os.environ.get('MONGO_URI')
    DEBUG = os.environ.get('DEBUG')