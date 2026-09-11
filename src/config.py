"""
Modulo de configuracion para el agente SRE con LiteLLM y Amazon Bedrock.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    model: str = os.getenv("LLM_MODEL", "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0")
    is_mock: bool = os.getenv("BEDROCK_MOCK", "true").lower() in ("true", "1", "yes")
    aws_region: str = os.getenv("AWS_REGION_NAME", "us-east-1")
    temperature: float = 0.1
    max_tokens: int = 2048


settings = Settings()
