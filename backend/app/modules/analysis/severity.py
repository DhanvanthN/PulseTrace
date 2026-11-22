def classify_severity(
    *,
    anomaly_type: str,
    z_score: float | None = None,
    critical_count: int = 0,
    error_count: int = 0,
    if_score: float | None = None,
) -> str:
    if critical_count >= 5 or (z_score is not None and z_score >= 4 and anomaly_type == "critical_spike"):
        return "CRITICAL"
    if critical_count >= 1 or error_count >= 20 or (z_score is not None and z_score >= 3.5):
        return "HIGH"
    if error_count >= 5 or (z_score is not None and z_score >= 2.5) or (if_score is not None and if_score > 0.65):
        return "MEDIUM"
    return "LOW"