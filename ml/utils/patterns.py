"""
ML pattern analysis: predict peak hours from historical data.
Used by the analytics service and report generator.
"""
from typing import List, Dict, Optional
from collections import defaultdict
import math


def predict_peak_hours(hourly_data: List[Dict]) -> List[int]:
    """
    Given a list of {'hour': str_iso, 'avg': float} records,
    return the top 3 predicted peak hours as integers (0–23).
    """
    hour_totals: Dict[int, List[float]] = defaultdict(list)
    for record in hourly_data:
        try:
            hour_str = record.get("hour", "")
            if "T" in hour_str:
                hour = int(hour_str.split("T")[1][:2])
            else:
                hour = int(hour_str[:2]) if hour_str else 0
            hour_totals[hour].append(float(record.get("avg", 0)))
        except (ValueError, IndexError):
            continue

    avg_by_hour = {h: sum(vals) / len(vals) for h, vals in hour_totals.items() if vals}
    sorted_hours = sorted(avg_by_hour.keys(), key=lambda h: avg_by_hour[h], reverse=True)
    return sorted_hours[:3]


def detect_traffic_pattern(hourly_data: List[Dict]) -> str:
    """
    Classify traffic pattern as: morning_peak, evening_peak, midday_peak,
    continuous_high, continuous_low, or unknown.
    """
    if not hourly_data:
        return "unknown"

    hour_avgs: Dict[int, float] = {}
    for record in hourly_data:
        try:
            hour_str = record.get("hour", "")
            if "T" in hour_str:
                hour = int(hour_str.split("T")[1][:2])
            else:
                hour = int(hour_str[:2]) if hour_str else 0
            hour_avgs[hour] = float(record.get("avg", 0))
        except (ValueError, IndexError):
            continue

    if not hour_avgs:
        return "unknown"

    overall_avg = sum(hour_avgs.values()) / len(hour_avgs)

    morning = sum(hour_avgs.get(h, 0) for h in range(6, 12)) / 6
    midday = sum(hour_avgs.get(h, 0) for h in range(11, 15)) / 4
    evening = sum(hour_avgs.get(h, 0) for h in range(17, 22)) / 5

    if overall_avg > 30:
        return "continuous_high"
    if overall_avg < 5:
        return "continuous_low"
    if morning > midday and morning > evening:
        return "morning_peak"
    if evening > morning and evening > midday:
        return "evening_peak"
    if midday > morning and midday > evening:
        return "midday_peak"
    return "unknown"


def estimate_next_peak(hourly_data: List[Dict], current_hour: int) -> Optional[int]:
    """
    Given current hour, estimate the next likely peak hour.
    Returns None if unpredictable.
    """
    peaks = predict_peak_hours(hourly_data)
    future_peaks = [h for h in peaks if h > current_hour]
    return future_peaks[0] if future_peaks else (peaks[0] if peaks else None)


def compute_anomaly_score(current_count: int, historical_avg: float) -> float:
    """
    Returns a score 0.0–1.0 indicating how anomalous current_count is
    relative to the historical average. Above 0.7 = anomaly.
    """
    if historical_avg <= 0:
        return 0.0
    ratio = current_count / historical_avg
    # Sigmoid-like score
    score = 1 / (1 + math.exp(-2 * (ratio - 2)))
    return round(min(1.0, max(0.0, score)), 3)
