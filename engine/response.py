from dataclasses import dataclass

from config import DRY_RUN


@dataclass
class ResponseResult:

    action: str
    executed: bool
    verified: bool
    message: str


class ThreatResponder:

    def respond(
        self,
        pid: int,
        process_name: str,
        risk_level: str
    ) -> ResponseResult:

        if risk_level == "NORMAL":

            return ResponseResult(
                action="ALLOW",
                executed=False,
                verified=True,
                message="Process considered normal."
            )

        if risk_level == "MEDIUM":

            return ResponseResult(
                action="ALERT",
                executed=True,
                verified=True,
                message=(
                    f"Alert generated for "
                    f"{process_name} (PID {pid})."
                )
            )

        if risk_level == "HIGH":

            if DRY_RUN:

                return ResponseResult(
                    action="CONTAIN_PROCESS",
                    executed=False,
                    verified=True,
                    message=(
                        f"DRY RUN: Would contain "
                        f"{process_name} "
                        f"(PID {pid})."
                    )
                )

            # Real process termination deliberately
            # remains disabled in V1.
            return ResponseResult(
                action="CONTAIN_PROCESS",
                executed=False,
                verified=False,
                message=(
                    "Real containment is disabled "
                    "for this V1 implementation."
                )
            )

        return ResponseResult(
            action="NONE",
            executed=False,
            verified=False,
            message="Unknown risk level."
        )