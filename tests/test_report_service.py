def test_report_service_builds_analysis():
    from backend.app.services.report_service import ReportService

    svc = ReportService()
    assert hasattr(svc, "build_daily_analysis")
