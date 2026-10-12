\
def severity_from_area_ratio(area_ratio: float) -> str:
    """Visual severity only; not real pothole depth."""
    if area_ratio < 0.015:
        return "LOW"
    if area_ratio < 0.05:
        return "MEDIUM"
    return "HIGH"
