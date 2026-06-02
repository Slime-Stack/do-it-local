"""Schema for Scanner Agent output."""

from dataclasses import dataclass, field


@dataclass
class ServiceInfo:
    name: str
    language: str = ""
    framework: str = ""
    port: int | None = None
    dockerfile: str = ""


@dataclass
class DatabaseInfo:
    type: str  # postgres, mysql, mongodb, etc.
    name: str = ""
    port: int | None = None
    connection_env_var: str = ""


@dataclass
class QueueInfo:
    type: str  # redis, rabbitmq, kafka, etc.
    name: str = ""
    port: int | None = None
    connection_env_var: str = ""


@dataclass
class EnvVarInfo:
    name: str
    source_file: str = ""
    is_secret: bool = False
    description: str = ""


@dataclass
class ScanResult:
    services: list[ServiceInfo] = field(default_factory=list)
    databases: list[DatabaseInfo] = field(default_factory=list)
    queues: list[QueueInfo] = field(default_factory=list)
    caches: list[QueueInfo] = field(default_factory=list)
    env_vars: list[EnvVarInfo] = field(default_factory=list)
    external_apis: list[str] = field(default_factory=list)
    language_stack: list[str] = field(default_factory=list)
    file_tree_summary: str = ""
    config_files_read: list[str] = field(default_factory=list)
