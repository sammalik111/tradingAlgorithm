import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://trading:trading@localhost:5432/trading")
os.environ.setdefault("AWS_REGION", "us-east-1")
