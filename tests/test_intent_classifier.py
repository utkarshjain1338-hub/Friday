from intents.intent_classifier import IntentClassifier


def test_intent_classifier_detects_workflow():
    classifier = IntentClassifier()
    intent, category, score = classifier.classify("Please start coding mode")
    assert intent == "coding_mode"
    assert category == "automation_request"
    assert score >= 0.5


def test_intent_classifier_detects_browser_control():
    classifier = IntentClassifier()
    intent, category, score = classifier.classify("Search Google for python tutorials")
    assert category == "browser_control"


def test_intent_classifier_returns_unknown_for_blank():
    classifier = IntentClassifier()
    intent, category, score = classifier.classify("")
    assert intent == "unknown"
    assert category == "general"
    assert score == 0.0
