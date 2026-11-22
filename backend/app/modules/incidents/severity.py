"""Documented incident severity aggregation from linked anomaly severities."""

SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def aggregate_incident_severity(anomaly_severities: list[str]) -> str:
    """
    Rules:
    - Any CRITICAL anomaly -> incident CRITICAL
    - Two or more HIGH severities -> incident HIGH
    - One HIGH plus two MEDIUM -> incident HIGH
    - Three or more MEDIUM -> incident HIGH
    - Any remaining HIGH alone -> HIGH
    - Any MEDIUM -> MEDIUM
    - Otherwise LOW
    """
    if not anomaly_severities:
        return "LOW"
    normalized = [value.upper() for value in anomaly_severities if value]
    if "CRITICAL" in normalized:
        return "CRITICAL"
    high_count = normalized.count("HIGH")
    medium_count = normalized.count("MEDIUM")
    if high_count >= 2:
        return "HIGH"
    if high_count >= 1 and medium_count >= 2:
        return "HIGH"
    if medium_count >= 3:
        return "HIGH"
    if high_count >= 1:
        return "HIGH"
    if medium_count >= 1:
        return "MEDIUM"
    return "LOW"