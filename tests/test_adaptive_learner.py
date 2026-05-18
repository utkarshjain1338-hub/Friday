from learning.adaptive_learner import AdaptiveLearner


def test_adaptive_learner_tracks_command():
    learner = AdaptiveLearner()
    learner.track_command("open browser")
    assert "open browser" in learner.command_history


def test_adaptive_learner_suggests_routine_for_repeated_commands():
    learner = AdaptiveLearner()
    for _ in range(5):
        learner.track_command("open browser")
    suggestion = learner.suggest_routine()
    assert suggestion is not None
    assert "open browser" in suggestion
