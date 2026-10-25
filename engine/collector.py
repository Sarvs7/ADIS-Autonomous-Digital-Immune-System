from queue import Empty

from engine.event_bus import EventBus
from engine.pipeline import DetectionPipeline
from engine.response import ThreatResponder
from memory.database import SecurityDatabase


class EventCollector:

    def __init__(
        self,
        event_bus: EventBus,
        pipeline: DetectionPipeline
    ):

        self.event_bus = event_bus
        self.pipeline = pipeline

        self.database = SecurityDatabase()

        self.responder = ThreatResponder()

        self.running = False

    def process_once(self):

        try:
            event = self.event_bus.get(
                timeout=0.5
            )

        except Empty:
            return None

        result = self.pipeline.process_event(
            event
        )

        return event, result

    def run(self):

        self.running = True

        while self.running:

            try:

                output = self.process_once()

                if output is None:
                    continue

                event, result = output

                event_id = self.database.save_event(
                    event
                )

                if result is not None:

                    risk = result.get("risk")

                    if risk is not None:

                        self.database.save_assessment(
                            event_id,
                            event,
                            risk
                        )

                        self.handle_result(
                            result
                        )

            except Exception as error:

                print(
                    f"Collector error: {error}"
                )

    def handle_result(self, result):

        risk = result.get("risk")

        if risk is None:
            return

        if risk.level == "NORMAL":
            return

        print(
            f"[DETECTION] "
            f"PID={result['pid']} "
            f"PROCESS={result['process_name']} "
            f"RISK={risk.score} "
            f"LEVEL={risk.level}"
        )

        for reason in risk.reasons:

            print(
                f"  Reason: {reason}"
            )

        response = self.responder.respond(
            pid=result["pid"],
            process_name=result["process_name"],
            risk_level=risk.level
        )

        print(
            f"[RESPONSE] "
            f"ACTION={response.action} "
            f"EXECUTED={response.executed} "
            f"VERIFIED={response.verified}"
        )

        print(
            f"  {response.message}"
        )

    def stop(self):

        self.running = False

        self.database.close()