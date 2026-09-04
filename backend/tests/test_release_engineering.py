from app.release_engineering import check_required_environment, summarize_readiness, sanitize_error_message

def test_required_environment_passes_with_strong_secret():
    result = summarize_readiness(check_required_environment({"AUTH_SECRET_KEY": "x" * 64, "AUTH_ALGORITHM": "HS256"}))
    assert result["ready"] is True

def test_required_environment_rejects_missing_secret():
    result = summarize_readiness(check_required_environment({"AUTH_SECRET_KEY": "", "AUTH_ALGORITHM": "HS256"}))
    assert result["ready"] is False

def test_required_environment_rejects_short_secret():
    result = summarize_readiness(check_required_environment({"AUTH_SECRET_KEY": "too-short", "AUTH_ALGORITHM": "HS256"}))
    assert result["ready"] is False

def test_sanitize_error_message_compacts_and_limits():
    value = sanitize_error_message("hello   world\n" + ("x" * 500))
    assert value.startswith("hello world")
    assert len(value) == 240

def test_readiness_summary_is_deterministic():
    env = {"AUTH_SECRET_KEY": "y" * 64, "AUTH_ALGORITHM": "HS256"}
    assert summarize_readiness(check_required_environment(env)) == summarize_readiness(check_required_environment(env))
