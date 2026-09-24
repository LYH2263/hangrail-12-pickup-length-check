import os

# 必须在 app.config / app.database 被导入前设置：测试不依赖 Postgres
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SEED_ON_EMPTY", "false")
