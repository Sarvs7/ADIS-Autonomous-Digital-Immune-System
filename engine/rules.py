from dataclasses import dataclass


@dataclass
class RuleResult:

    rule_name: str
    triggered: bool
    score: int
    reason: str


def evaluate_rules(summary: dict) -> list[RuleResult]:

    results = []

    process_starts = summary.get(
        "process_starts", 0
    )

    file_creates = summary.get(
        "file_creates", 0
    )

    file_modifies = summary.get(
        "file_modifies", 0
    )

    file_deletes = summary.get(
        "file_deletes", 0
    )

    network_connections = summary.get(
        "network_connections", 0
    )

    # Rule 1: unusually high process creation
    triggered = process_starts >= 10

    results.append(
        RuleResult(
            rule_name="high_process_creation",
            triggered=triggered,
            score=20 if triggered else 0,
            reason=(
                "Large number of processes "
                "created in the behavior window."
                if triggered
                else "Process creation is within normal range."
            ),
        )
    )

    # Rule 2: large amount of file modification
    triggered = file_modifies >= 50

    results.append(
        RuleResult(
            rule_name="high_file_modification",
            triggered=triggered,
            score=30 if triggered else 0,
            reason=(
                "Large number of file modifications "
                "detected."
                if triggered
                else "File modification activity is within normal range."
            ),
        )
    )

    # Rule 3: large amount of file creation
    triggered = file_creates >= 50

    results.append(
        RuleResult(
            rule_name="high_file_creation",
            triggered=triggered,
            score=25 if triggered else 0,
            reason=(
                "Large number of files created."
                if triggered
                else "File creation activity is within normal range."
            ),
        )
    )

    # Rule 4: large amount of deletion
    triggered = file_deletes >= 30

    results.append(
        RuleResult(
            rule_name="high_file_deletion",
            triggered=triggered,
            score=35 if triggered else 0,
            reason=(
                "Large number of file deletions detected."
                if triggered
                else "File deletion activity is within normal range."
            ),
        )
    )

    # Rule 5: unusually high network activity
    triggered = network_connections >= 20

    results.append(
        RuleResult(
            rule_name="high_network_activity",
            triggered=triggered,
            score=20 if triggered else 0,
            reason=(
                "Large number of network connections detected."
                if triggered
                else "Network activity is within normal range."
            ),
        )
    )

    return results