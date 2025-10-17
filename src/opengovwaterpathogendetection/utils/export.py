"""Data export utilities for various formats."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class DataExporter:
    """Export data to various formats (CSV, JSON, Excel-compatible)."""

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize exporter with output directory."""
        self.output_dir = Path(output_dir or "exports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_to_json(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """Export data to JSON format."""
        if not filename:
            filename = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info("data_exported_json", filepath=str(filepath), records=len(data))
        return str(filepath)

    def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        fieldnames: Optional[List[str]] = None
    ) -> str:
        """Export data to CSV format."""
        if not data:
            raise ValueError("No data to export")
        
        if not filename:
            filename = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.output_dir / filename
        
        # Use provided fieldnames or extract from first record
        if not fieldnames:
            fieldnames = list(data[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info("data_exported_csv", filepath=str(filepath), records=len(data))
        return str(filepath)

    def export_pathogen_report(
        self,
        pathogen_data: List[Dict],
        format: str = "json"
    ) -> str:
        """Export pathogen detection report."""
        report = {
            "report_type": "pathogen_detection",
            "generated_at": datetime.utcnow().isoformat(),
            "total_records": len(pathogen_data),
            "data": pathogen_data
        }
        
        if format == "csv":
            return self.export_to_csv(pathogen_data, "pathogen_report.csv")
        else:
            return self.export_to_json([report], "pathogen_report.json")

    def export_risk_assessment_report(
        self,
        assessments: List[Dict],
        summary: Dict
    ) -> str:
        """Export risk assessment report with summary."""
        report = {
            "report_type": "risk_assessment",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": summary,
            "assessments": assessments
        }
        
        filename = f"risk_assessment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        return self.export_to_json([report], filename)

    def export_compliance_report(
        self,
        data: List[Dict],
        compliance_standards: Dict
    ) -> str:
        """Export compliance report against standards."""
        report = {
            "report_type": "compliance",
            "generated_at": datetime.utcnow().isoformat(),
            "standards": compliance_standards,
            "data": data,
            "total_samples": len(data),
            "compliant_samples": sum(1 for d in data if d.get("compliant", False)),
            "non_compliant_samples": sum(1 for d in data if not d.get("compliant", True))
        }
        
        filename = f"compliance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        return self.export_to_json([report], filename)

    def export_summary_statistics(
        self,
        stats: Dict[str, Any]
    ) -> str:
        """Export summary statistics."""
        report = {
            "report_type": "summary_statistics",
            "generated_at": datetime.utcnow().isoformat(),
            "statistics": stats
        }
        
        filename = f"statistics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        return self.export_to_json([report], filename)
