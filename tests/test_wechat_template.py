def test_build_wechat_template_data():
    from backend.app.jobs.poll_garmin import build_template_data

    data = build_template_data("2026-01-01", "报告已生成")
    assert "thing1" in data
