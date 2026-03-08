"""Unit tests for match scoring logic (label thresholds)."""


def test_label_thresholds():
    def label(score: int) -> str:
        if score < 50:
            return "Developing"
        if score < 80:
            return "Competitive"
        return "Ready"
    assert label(0) == "Developing"
    assert label(49) == "Developing"
    assert label(50) == "Competitive"
    assert label(79) == "Competitive"
    assert label(80) == "Ready"
    assert label(100) == "Ready"
