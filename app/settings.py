"""Environment-backed settings."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings:
    def __init__(self) -> None:
        self.vllm_base_url: str = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        self.vllm_api_key: str = os.getenv("VLLM_API_KEY", "not-a-real-key")
        # Live default is gpt-oss-120b (Harmony). Qwen3-8B remains a supported dense path.
        self.model_name: str = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")
        # Optional. Record the served revision at launch in reports/environment.json.
        self.model_revision: str = os.getenv("MODEL_REVISION", "")
        self.reasoning_effort: str = os.getenv("REASONING_EFFORT", "low")
        self.vllm_docker_image: str = os.getenv("VLLM_DOCKER_IMAGE", "vllm/vllm-openai:latest")
        self.vllm_docker_digest: str = os.getenv("VLLM_DOCKER_DIGEST", "")
        self.vllm_batch_invariant: str = os.getenv("VLLM_BATCH_INVARIANT", "1")
        self.database_url: str = os.getenv(
            "DATABASE_URL", f"sqlite:///{REPO_ROOT / 'accounting_agent.db'}"
        )
        self.ap_account: str = os.getenv("AP_ACCOUNT", "2000")
        self.prompt_version: str = os.getenv("PROMPT_VERSION", "invoice_extraction_v1")
        self.schema_version: str = os.getenv("SCHEMA_VERSION", "1.0.0")
        self.policy_path: Path = Path(
            os.getenv("POLICY_PATH", str(REPO_ROOT / "config" / "policy.yaml"))
        )
        if not self.policy_path.is_absolute():
            self.policy_path = REPO_ROOT / self.policy_path
        self.temperature: float = float(os.getenv("TEMPERATURE", "0"))
        self.top_p: float = float(os.getenv("TOP_P", "1"))
        self.seed: int = int(os.getenv("SEED", "42"))
        self.prompt_path: Path = REPO_ROOT / "prompts" / f"{self.prompt_version}.txt"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
