from engine.anomaly import AnomalyDetector


def test_anomaly_detector():

    detector = AnomalyDetector(
        "models/test_anomaly_model.pkl"
    )

    normal_vectors = [
        [10, 0, 0, 10, 2, 5, 0, 5],
        [11, 0, 0, 11, 2, 6, 0, 6],
        [9, 0, 0, 9, 1, 4, 0, 4],
        [10, 0, 0, 10, 3, 5, 0, 5],
        [12, 0, 0, 12, 2, 7, 0, 6],
        [8, 0, 0, 8, 1, 3, 0, 3],
    ]

    detector.train(
        normal_vectors
    )

    score = detector.predict(
        [10, 0, 0, 10, 2, 5, 0, 5]
    )

    assert isinstance(
        score,
        float
    )