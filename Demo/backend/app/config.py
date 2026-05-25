from pathlib import Path
from pydantic_settings import BaseSettings

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./reconciliation.db"
    reports_dir: str = "../reports"
    uploads_dir: str = "../uploads"
    sample_data_dir: str = ""
    tolerance: float = 0.01
    log_level: str = "INFO"
    cors_origins: str = (
        "http://localhost:5173,http://localhost:3000,"
        "https://payment-reconciliation-system.vercel.app"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def reports_path(self) -> Path:
        return Path(self.reports_dir).resolve()

    @property
    def uploads_path(self) -> Path:
        return Path(self.uploads_dir).resolve()

    @property
    def sample_data_path(self) -> Path:
        candidates: list[Path] = []
        if self.sample_data_dir.strip():
            candidates.append(Path(self.sample_data_dir).resolve())
        candidates.extend(
            (
                _BACKEND_ROOT / "sample_data",
                _BACKEND_ROOT.parent / "sample_data",
            )
        )
        for path in candidates:
            if path.is_dir():
                return path.resolve()
        return candidates[0] if candidates else (_BACKEND_ROOT / "sample_data").resolve()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
