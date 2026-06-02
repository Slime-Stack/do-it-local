"""Tests for generated config validation."""
from backend.validation import (
    scan_for_secrets,
    validate_docker_compose,
    validate_env_file,
    validate_yaml,
)


def test_validate_yaml_valid():
    assert validate_yaml("services:\n  web:\n    image: nginx") == []


def test_validate_yaml_invalid():
    errors = validate_yaml("services:\n  web:\n    - invalid: [")
    assert len(errors) > 0


def test_validate_docker_compose_valid():
    content = "services:\n  web:\n    image: nginx:1.25\n    ports:\n      - '80:80'"
    assert validate_docker_compose(content) == []


def test_validate_docker_compose_missing_services():
    errors = validate_docker_compose("version: '3'")
    assert any("services" in e for e in errors)


def test_validate_env_file_valid():
    assert validate_env_file("DB_HOST=localhost\nDB_PORT=5432\n# comment\n") == []


def test_validate_env_file_invalid():
    errors = validate_env_file("DB_HOST=localhost\nbad line\n")
    assert len(errors) == 1


def test_scan_for_secrets_clean():
    assert scan_for_secrets("DB_HOST=localhost") == []


def test_scan_for_secrets_finds_pattern():
    # Use a GitHub PAT pattern (fake) to test detection without triggering push protection
    findings = scan_for_secrets("TOKEN=ghp_aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2")
    assert len(findings) > 0
