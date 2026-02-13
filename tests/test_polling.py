def test_poll_detects_new_activity():
    from backend.app.jobs.poll_garmin import detect_new_data

    assert detect_new_data({}, {}) is False
