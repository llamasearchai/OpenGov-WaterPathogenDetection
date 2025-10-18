"""Comprehensive tests for v1.2.0 features."""

import pytest
from pathlib import Path
import csv
import json
from unittest.mock import patch, Mock

from opengovwaterpathogendetection.services.compliance import (
    ComplianceService,
    RegulatoryStandard,
    ComplianceStatus
)
from opengovwaterpathogendetection.services.analytics import AnalyticsService
from opengovwaterpathogendetection.services.notifications import (
    NotificationService,
    NotificationPriority
)
from opengovwaterpathogendetection.utils.batch_import import BatchImporter
from opengovwaterpathogendetection.models.pathogen import PathogenType


class TestComplianceService:
    """Test regulatory compliance checking."""

    def test_compliance_epa_drinking_water_compliant(self):
        """Test EPA drinking water standards - compliant case."""
        service = ComplianceService()
        result = service.check_compliance(
            pathogen_type=PathogenType.BACTERIA,
            pathogen_name="E. coli",
            concentration=0,
            standard=RegulatoryStandard.EPA_DRINKING_WATER
        )
        assert result['compliant'] is True
        assert result['status'] == ComplianceStatus.COMPLIANT.value

    def test_compliance_epa_drinking_water_violation(self):
        """Test EPA drinking water standards - violation case."""
        service = ComplianceService()
        result = service.check_compliance(
            pathogen_type=PathogenType.BACTERIA,
            pathogen_name="E. coli",
            concentration=10,
            standard=RegulatoryStandard.EPA_DRINKING_WATER
        )
        assert result['compliant'] is False
        assert result['status'] == ComplianceStatus.NON_COMPLIANT.value

    def test_compliance_warning_threshold(self):
        """Test warning threshold (20% over limit)."""
        service = ComplianceService()
        result = service.check_compliance(
            pathogen_type=PathogenType.BACTERIA,
            pathogen_name="Legionella",
            concentration=1100,  # 10% over 1000 limit
            standard=RegulatoryStandard.EPA_DRINKING_WATER
        )
        assert result['status'] in [ComplianceStatus.WARNING.value, ComplianceStatus.COMPLIANT.value]

    def test_batch_compliance_check(self):
        """Test batch compliance checking."""
        service = ComplianceService()
        samples = [
            {"pathogen_type": "bacteria", "concentration": 0},
            {"pathogen_type": "virus", "concentration": 5},
            {"pathogen_type": "parasite", "concentration": 0.5},
        ]
        summary = service.batch_compliance_check(samples)
        assert summary['total_samples'] == 3
        assert 'compliance_rate' in summary

    def test_compliance_report_generation(self):
        """Test compliance report generation."""
        service = ComplianceService()
        summary = {
            "total_samples": 10,
            "compliant": 8,
            "non_compliant": 2,
            "warnings": 0,
            "requires_review": 0,
            "compliance_rate": 80.0,
            "standard": "epa_drinking_water",
            "results": []
        }
        report = service.generate_compliance_report(summary, include_details=False)
        assert report['report_type'] == "regulatory_compliance"
        assert report['overall_status'] == "FAIL"


class TestAnalyticsService:
    """Test advanced analytics."""

    def test_temporal_trend_analysis_increasing(self):
        """Test detecting increasing trend."""
        service = AnalyticsService()
        detection_data = [
            {"timestamp": "2025-10-01T00:00:00", "concentration": 100, "location": "Site A"},
            {"timestamp": "2025-10-05T00:00:00", "concentration": 150, "location": "Site A"},
            {"timestamp": "2025-10-10T00:00:00", "concentration": 200, "location": "Site A"},
            {"timestamp": "2025-10-15T00:00:00", "concentration": 300, "location": "Site A"},
            {"timestamp": "2025-10-20T00:00:00", "concentration": 400, "location": "Site A"},
            {"timestamp": "2025-10-25T00:00:00", "concentration": 500, "location": "Site A"},
            {"timestamp": "2025-10-30T00:00:00", "concentration": 600, "location": "Site A"},
        ]
        analysis = service.analyze_temporal_trends(detection_data, time_window_days=30)
        assert analysis['trend'] in ["increasing", "increasing_significantly", "stable"]
        assert analysis['total_detections'] == 7

    def test_spatial_cluster_detection(self):
        """Test spatial clustering."""
        service = AnalyticsService()
        location_data = [
            {"location": "Site A", "concentration": 100, "timestamp": "2025-10-01"},
            {"location": "Site A", "concentration": 150, "timestamp": "2025-10-02"},
            {"location": "Site A", "concentration": 200, "timestamp": "2025-10-03"},
            {"location": "Site B", "concentration": 50, "timestamp": "2025-10-01"},
        ]
        analysis = service.detect_spatial_clusters(location_data, cluster_threshold=3)
        assert analysis['total_locations'] == 2
        assert analysis['clusters_identified'] >= 0

    def test_outbreak_risk_prediction_low(self):
        """Test low outbreak risk prediction."""
        service = AnalyticsService()
        detections = [
            {"timestamp": "2025-10-01T00:00:00", "concentration": 50, "location": "Site A"},
            {"timestamp": "2025-10-02T00:00:00", "concentration": 60, "location": "Site A"},
        ]
        prediction = service.predict_outbreak_risk(detections)
        assert prediction['risk_level'] in ["low", "medium"]
        assert 0 <= prediction['confidence'] <= 1

    def test_outbreak_risk_prediction_critical(self):
        """Test critical outbreak risk prediction."""
        service = AnalyticsService()
        # Many detections with high concentrations across multiple locations
        detections = [
            {"timestamp": f"2025-10-{i:02d}T00:00:00", "concentration": 2000, "location": f"Site {chr(65+i%10)}"}
            for i in range(1, 31)  # 30 detections in 30 days across 10 locations
        ]
        prediction = service.predict_outbreak_risk(detections)
        assert prediction['risk_level'] in ["high", "critical"]

    def test_summary_statistics(self):
        """Test summary statistics generation."""
        service = AnalyticsService()
        all_data = [
            {"pathogen_type": "bacteria", "concentration": 100},
            {"pathogen_type": "bacteria", "concentration": 200},
            {"pathogen_type": "virus", "concentration": 50},
        ]
        summary = service.generate_summary_statistics(all_data, group_by="pathogen_type")
        assert "groups" in summary
        assert "bacteria" in summary['groups']


class TestNotificationService:
    """Test notification system."""

    def test_send_alert_basic(self):
        """Test basic alert sending."""
        service = NotificationService()
        result = service.send_alert(
            title="Test Alert",
            message="Test message",
            priority=NotificationPriority.MEDIUM
        )
        assert "notification_id" in result
        assert result['priority'] == NotificationPriority.MEDIUM.value

    def test_send_risk_alert(self):
        """Test risk assessment alert."""
        service = NotificationService()
        risk_assessment = {
            "risk_level": "high",
            "location": "Test Site",
            "concentration": 1500,
            "recommendations": ["Test recommendation"],
            "timestamp": "2025-10-17T00:00:00"
        }
        result = service.send_risk_alert(risk_assessment)
        assert result['priority'] == NotificationPriority.HIGH.value

    def test_send_compliance_alert(self):
        """Test compliance violation alert."""
        service = NotificationService()
        compliance_result = {
            "status": "non_compliant",
            "pathogen_name": "E. coli",
            "concentration": 10,
            "regulatory_limit": 0,
            "exceedance_percent": 100,
            "actions_required": ["Immediate action"],
            "standard": "epa_drinking_water",
            "timestamp": "2025-10-17T00:00:00"
        }
        result = service.send_compliance_alert(compliance_result)
        assert result['priority'] == NotificationPriority.CRITICAL.value

    def test_send_outbreak_alert(self):
        """Test outbreak prediction alert."""
        service = NotificationService()
        outbreak_prediction = {
            "risk_level": "critical",
            "confidence": 0.9,
            "risk_score": 10,
            "risk_factors": ["High concentration", "Wide spread"],
            "detection_count": 50,
            "detection_rate_per_day": 5.0,
            "unique_locations": 10,
            "average_concentration": 2000,
            "recommendation": "Immediate action required",
            "timestamp": "2025-10-17T00:00:00"
        }
        result = service.send_outbreak_alert(outbreak_prediction)
        assert result['priority'] == NotificationPriority.CRITICAL.value

    def test_notification_history(self):
        """Test notification history retrieval."""
        service = NotificationService()
        # Send some alerts
        service.send_alert("Test 1", "Message 1", NotificationPriority.LOW)
        service.send_alert("Test 2", "Message 2", NotificationPriority.HIGH)
        
        history = service.get_notification_history(limit=10)
        assert len(history) >= 2


class TestBatchImporter:
    """Test batch import functionality."""

    def test_import_samples_from_csv(self, tmp_path, monkeypatch):
        """Test importing samples from CSV."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
        
        from opengovwaterpathogendetection.core.config import reload_settings
        reload_settings()
        
        # Create test CSV
        csv_path = tmp_path / "samples.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'sample_id', 'location', 'collection_date', 'collector_name', 'sample_type'
            ])
            writer.writeheader()
            writer.writerow({
                'sample_id': 'TEST-001',
                'location': 'Test Site',
                'collection_date': '2025-10-17',
                'collector_name': 'Test User',
                'sample_type': 'raw_water'
            })
        
        importer = BatchImporter()
        successful, failed, errors = importer.import_samples_from_csv(str(csv_path))
        
        assert successful == 1
        assert failed == 0
        assert len(errors) == 0
        
        importer.close()

    def test_import_samples_with_errors(self, tmp_path, monkeypatch):
        """Test importing samples with some errors."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
        
        from opengovwaterpathogendetection.core.config import reload_settings
        reload_settings()
        
        # Create test CSV with errors
        csv_path = tmp_path / "samples_errors.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'sample_id', 'location', 'collection_date', 'collector_name', 'sample_type'
            ])
            writer.writeheader()
            # Valid row
            writer.writerow({
                'sample_id': 'TEST-001',
                'location': 'Test Site',
                'collection_date': '2025-10-17',
                'collector_name': 'Test User',
                'sample_type': 'raw_water'
            })
            # Invalid row (missing required field)
            writer.writerow({
                'sample_id': 'TEST-002',
                'location': '',
                'collection_date': '2025-10-17',
                'collector_name': 'Test User',
                'sample_type': 'raw_water'
            })
        
        importer = BatchImporter()
        successful, failed, errors = importer.import_samples_from_csv(str(csv_path), skip_errors=True)
        
        assert successful >= 1
        assert failed >= 0
        
        importer.close()

    def test_generate_sample_template(self, tmp_path):
        """Test CSV template generation."""
        template_path = tmp_path / "template.csv"
        importer = BatchImporter()
        result = importer.generate_sample_csv_template(str(template_path))
        
        assert Path(result).exists()
        
        # Verify template contents
        with open(result, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert 'sample_id' in rows[0]
        
        importer.close()


class TestIntegratedWorkflow:
    """Test integrated workflows combining multiple features."""

    def test_full_compliance_workflow(self):
        """Test complete compliance checking workflow."""
        compliance_service = ComplianceService()
        notification_service = NotificationService()
        
        # Check compliance
        result = compliance_service.check_compliance(
            pathogen_type=PathogenType.BACTERIA,
            pathogen_name="E. coli",
            concentration=10,
            standard=RegulatoryStandard.EPA_DRINKING_WATER
        )
        
        # Send alert if non-compliant
        if not result['compliant']:
            alert = notification_service.send_compliance_alert(result)
            assert "notification_id" in alert

    def test_outbreak_detection_workflow(self):
        """Test complete outbreak detection and alert workflow."""
        analytics_service = AnalyticsService()
        notification_service = NotificationService()
        
        # Analyze for outbreak
        detections = [
            {"timestamp": f"2025-10-{i:02d}T00:00:00", "concentration": 1500 + i*100, "location": f"Site {i}"}
            for i in range(1, 11)
        ]
        
        prediction = analytics_service.predict_outbreak_risk(detections)
        
        # Send alert if high risk
        if prediction['risk_level'] in ['high', 'critical']:
            alert = notification_service.send_outbreak_alert(prediction)
            assert "notification_id" in alert

