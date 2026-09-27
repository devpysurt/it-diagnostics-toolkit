"""Small, serializable report model shared by collectors and renderers."""

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Status = Literal["OK", "WARNING", "FAIL", "SKIP"]
STATUSES = ("OK", "WARNING", "FAIL", "SKIP")


@dataclass(frozen=True)
class Check:
    id: str
    category: str
    title: str
    status: Status
    summary: str
    recommendation: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"Unknown status: {self.status}")


@dataclass
class Report:
    generated_at: str
    mode: str
    inventory: dict[str, Any]
    checks: list[Check]
    tool_version: str

    @property
    def counts(self) -> dict[str, int]:
        return {status: sum(c.status == status for c in self.checks) for status in STATUSES}

    @property
    def overall_status(self) -> Status:
        for status in ("FAIL", "WARNING", "OK"):
            if self.counts[status]:
                return status
        return "SKIP"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            **asdict(self),
            "overall_status": self.overall_status,
            "counts": self.counts,
            "coverage": "partial" if self.counts["SKIP"] else "complete",
        }
