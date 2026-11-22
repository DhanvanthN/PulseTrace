import re
from typing import Any

_FORBIDDEN_KEY = re.compile(r"(password|secret|token|api[_-]?key|credential)", re.IGNORECASE)


def sanitize_configuration_diff(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip keys that look like secrets from deployment configuration diffs."""

    def _scrub(value: Any) -> Any:
        if isinstance(value, dict):
            cleaned: dict[str, Any] = {}
            for key, item in value.items():
                if _FORBIDDEN_KEY.search(key):
                    continue
                cleaned[key] = _scrub(item)
            return cleaned
        if isinstance(value, list):
            return [_scrub(item) for item in value]
        return value

    return _scrub(payload)