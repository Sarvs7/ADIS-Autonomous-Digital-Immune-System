from dataclasses import dataclass

from config import (
    LOW_RISK_THRESHOLD,
    MEDIUM_RISK_THRESHOLD,
    HIGH_RISK_THRESHOLD,
)

from engine.rules import RuleResult


@dataclass
class RiskAssessment:

    score: int
    level: str
    reasons: list[str]


def calculate_risk(
    rule_results: list[RuleResult],
    anomaly_score: float = 0.0
) -> RiskAssessment:

    rule_score = sum(
        result.score
        for result in rule_results
        if result.triggered
    )

    # Convert anomaly score into a 0-40 contribution.
    anomaly_contribution = int(
        max(
            0,
            min(
                40,
                anomaly_score * 40
            )
        )
    )

    total_score = min(
        100,
        rule_score + anomaly_contribution
    )

    if total_score >= HIGH_RISK_THRESHOLD:
        level = "HIGH"

    elif total_score >= MEDIUM_RISK_THRESHOLD:
        level = "MEDIUM"

    elif total_score >= LOW_RISK_THRESHOLD:
        level = "LOW"

    else:
        level = "NORMAL"

    reasons = [
        result.reason
        for result in rule_results
        if result.triggered
    ]

    if anomaly_contribution > 0:
        reasons.append(
            f"Anomaly detection contribution: "
            f"{anomaly_contribution}"
        )

    return RiskAssessment(
        score=total_score,
        level=level,
        reasons=reasons,
    )