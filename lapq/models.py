"""
lapq.models — Data classes for QPU-1 API responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class JobResult:
    """Result of a single QPU-1 job execution."""

    success: bool
    job_id: Optional[str]
    status: str
    output: str
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def bits(self) -> str:
        """
        Extract the measurement bit-string from the output.

        Parses the first line that looks like a binary string (only '0' and '1').
        """
        for line in self.output.strip().splitlines():
            cleaned = line.strip()
            if cleaned and all(c in "01" for c in cleaned):
                return cleaned
        return self.output.strip()

    def __bool__(self) -> bool:
        return self.success

    def __repr__(self) -> str:
        return (
            f"JobResult(success={self.success}, status={self.status!r}, "
            f"bits={self.bits!r})"
        )


@dataclass
class BatchResult:
    """Result of a batch execution (multiple circuits)."""

    success: bool
    results: List[JobResult] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def __iter__(self):
        return iter(self.results)

    def __len__(self):
        return len(self.results)

    def __getitem__(self, idx):
        return self.results[idx]

    def __bool__(self) -> bool:
        return self.success


@dataclass
class QuotaInfo:
    """Account quota information."""

    jobs_used_today: int = 0
    max_jobs_per_day: int = 0
    max_qubits_per_job: int = 0
    tier: str = "unknown"
    remaining: int = 0

    def __repr__(self) -> str:
        return (
            f"QuotaInfo(tier={self.tier!r}, used={self.jobs_used_today}, "
            f"remaining={self.remaining}, max_qubits={self.max_qubits_per_job})"
        )


@dataclass
class TranspileResult:
    """Result of a code transpilation request."""

    success: bool
    qreg_code: str = ""
    original_format: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.success


@dataclass
class ValidateResult:
    """Result of a code validation request."""

    success: bool
    valid: bool = False
    issues: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.valid
