from typing import Any
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import dotenv

dotenv.load_dotenv(override=True)


class AppSettings(BaseSettings):
    model_config = ConfigDict(
        validate_assignment=True,
        extra="ignore",
        env_file=".env",
    )

    # fastapi_kwargs
    debug: bool = False
    docs_url: str = "/docs"
    openapi_prefix: str = ""
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    title: str = "ST Automation application"
    version: str = "0.0.1"

    # back-end app settings
    app_name: str = "Laptrinhai Mezon Bot"
    api_v1_prefix: str = "/api/v1"
    jwt_token_prefix: str = "bearer"
    allowed_hosts: list[str] = ["*"]

    app_env: str
    # Database settings
    db_uri: str

    # Mezon Bot settings
    mezon_client_id: str
    mezon_api_key: str
    mezon_bot_require_mention: bool = False

    # S3-compatible storage settings (optional)
    s3_endpoint_url: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket_name: str | None = None
    s3_region: str = "auto"
    s3_public_url_base: str | None = None

    @property
    def fastapi_kwargs(self) -> dict[str, Any]:
        kwargs = {
            "debug": self.debug,
            "title": self.title,
            "version": self.version,
        }
        if self.app_env == "dev":
            kwargs.update(
                {
                    "docs_url": self.docs_url,
                    "openapi_prefix": self.openapi_prefix,
                    "openapi_url": self.openapi_url,
                    "redoc_url": self.redoc_url,
                }
            )
        return kwargs


app_settings = AppSettings()
