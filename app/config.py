import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Environment-backed configuration shared by API scripts and Render."""

    database_url = os.getenv("DATABASE_URL", "")
    port = int(os.getenv("PORT", "8000"))
    seed_demo_data = os.getenv("SEED_DEMO_DATA", "false").lower() == "true"

    def validate(self) -> None:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is required. Copy .env.example to .env and set it.")


settings = Settings()
