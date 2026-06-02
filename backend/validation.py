"""Validation for generated configuration files."""

import re

SECRET_PATTERNS = [
    r"sk_live_[a-zA-Z0-9]{20,}",
    r"sk-[a-zA-Z0-9]{20,}",
    r"ghp_[a-zA-Z0-9]{36}",
    r"glpat-[a-zA-Z0-9\-_]{20}",
    r"AKIA[A-Z0-9]{16}",
    r"xox[baprs]-[a-zA-Z0-9\-]{10,}",
]


def validate_yaml(content: str) -> list[str]:
    errors = []
    try:
        from ruamel.yaml import YAML

        yaml = YAML()
        doc = yaml.load(content)
        if doc is None:
            errors.append("YAML parsed but is empty")
    except Exception as e:
        errors.append(f"YAML parse error: {e}")
    return errors


def validate_docker_compose(content: str) -> list[str]:
    errors = validate_yaml(content)
    if errors:
        return errors

    from ruamel.yaml import YAML

    yaml = YAML()
    doc = yaml.load(content)

    if not isinstance(doc, dict):
        return ["docker-compose must be a YAML mapping"]
    if "services" not in doc:
        errors.append("docker-compose missing 'services' key")

    return errors


def validate_env_file(content: str) -> list[str]:
    errors = []
    for i, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            errors.append(f"Line {i}: missing '=' separator")
    return errors


def scan_for_secrets(content: str) -> list[str]:
    findings = []
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            findings.append(
                f"Potential secret pattern found: {pattern} ({len(matches)} matches)"
            )
    return findings
