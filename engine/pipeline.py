from engine.anomaly import AnomalyDetector
from engine.behavior import BehaviorCorrelator
from engine.event_normalizer import EventNormalizer
from engine.events import SecurityEvent
from engine.features import feature_vector
from engine.rules import evaluate_rules
from engine.risk import calculate_risk


class DetectionPipeline:

    def __init__(
        self,
        anomaly_model_path="models/anomaly_model.pkl"
    ):

        self.correlator = BehaviorCorrelator(
            window_seconds=60
        )

        self.normalizer = EventNormalizer(
            duplicate_window_ms=100
        )

        self.anomaly_detector = AnomalyDetector(
            anomaly_model_path
        )

        self.anomaly_model_available = False

        try:
            self.anomaly_detector.load()
            self.anomaly_model_available = True

        except FileNotFoundError:
            # ADIS can operate using rules
            # until a trained model exists.
            self.anomaly_model_available = False

    def process_event(
        self,
        event: SecurityEvent
    ):

        event = self.normalizer.normalize(
            event
        )

        if event is None:
            return None

        self.correlator.add_event(
            event
        )

        if event.pid is None:
            return {
                "event": event,
                "pid": None,
                "risk": None,
            }

        summary = self.correlator.summarize(
            event.pid
        )

        vector = feature_vector(
            summary
        )

        rule_results = evaluate_rules(
            summary
        )

        anomaly_contribution = 0

        if self.anomaly_model_available:

            anomaly_contribution = (
                self.anomaly_detector
                .anomaly_contribution(vector)
            )

        assessment = calculate_risk(
            rule_results,
            anomaly_score=(
                anomaly_contribution / 40
            )
        )

        return {
            "event": event,
            "pid": event.pid,
            "process_name": event.process_name,
            "executable": event.executable,
            "summary": summary,
            "features": vector,
            "rules": rule_results,
            "anomaly_contribution":
                anomaly_contribution,
            "risk": assessment,
        }