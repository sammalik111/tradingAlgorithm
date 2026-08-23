import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://trading:trading@localhost:5432/trading")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
