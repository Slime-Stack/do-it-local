"""Schema for Detector Agent output."""
from dataclasses import dataclass, field


@dataclass
class PIIField:
    field_name: str
    model_or_table: str
    pii_type: str  # email, phone, ssn, address, name, etc.
    risk_level: str = "medium"  # low, medium, high


@dataclass
class SideEffectService:
    name: str
    type: str  # email, sms, payment, webhook, etc.
    env_vars: list[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class DetectionResult:
    pii_fields: list[PIIField] = field(default_factory=list)
    side_effect_services: list[SideEffectService] = field(default_factory=list)
    compliance_flags: list[str] = field(default_factory=list)
    secret_placeholders: dict[str, str] = field(default_factory=dict)
    risk_summary: str = ""
