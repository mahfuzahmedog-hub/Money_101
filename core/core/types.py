from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    tier: str
    tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    success: bool = True


@dataclass
class Task:
    id: int = 0
    description: str = ""
    status: str = "pending"
    assigned_agent: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = ""


@dataclass
class Outcome:
    task_id: int = 0
    task_type: str = ""
    platform: str = ""
    niche: str = ""
    price: float = 0.0
    content_summary: str = ""
    posting_time: str = ""
    llm_tier_used: str = "standard"


@dataclass
class Directive:
    from_agent: str = ""
    directive_type: str = "proposal"
    action: str = ""
    reason: str = ""
    status: str = "pending"
