"""Schema for Generator Agent output."""

from dataclasses import dataclass, field


@dataclass
class GeneratedFile:
    path: str
    content: str
    description: str = ""


@dataclass
class GenerationResult:
    files_generated: list[GeneratedFile] = field(default_factory=list)
    branch_name: str = ""
    merge_request_url: str = ""
    summary: str = ""
