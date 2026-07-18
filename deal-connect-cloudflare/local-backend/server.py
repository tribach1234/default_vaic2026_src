from waitress import serve

from app import app
from config import Config

if __name__ == "__main__":
    print(f"Deal Connect API listening on http://{Config.HOST}:{Config.PORT}")
    serve(
        app,
        host=Config.HOST,
        port=Config.PORT,
        threads=max(4, Config.MAX_CONCURRENT_JOBS + 2),
        channel_timeout=300,
        cleanup_interval=30,
    )
