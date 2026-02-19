import os

class Settings:
    PROJECT_NAME: str = "Generate and Embed API"
    VERSION: str = "1.0.0"
    ENV: str = os.getenv("ENV", "dev")
    PORT: int = os.getenv("PORT", 8000)

    @property
    def DOCS_URL(self):
        # Hide docs if we are in production
        return None if self.ENV == "prod" else "/docs"

settings = Settings()