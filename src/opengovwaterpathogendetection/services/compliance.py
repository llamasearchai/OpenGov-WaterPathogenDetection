"""Automated compliance checking against regulatory standards."""

from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import structlog

from ..models.pathogen import PathogenType

logger = structlog.get_logger(__name__)


class RegulatoryStandard(str, Enum):
    """Regulatory standard types."""
    EPA_DRINKING_WATER = "epa_drinking_water"
    CDC_RECREATIONAL = "cdc_recreational"
    WHO_GUIDELINES = "who_guidelines"
    CALIFORNIA_TITLE_22 = "california_title_22"


class ComplianceStatus(str, Enum):
    """Compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    REQUIRES_REVIEW = "requires_review"


class ComplianceService:
    """Service for regulatory compliance checking."""

    # EPA Maximum Contaminant Levels (MCLs) for drinking water
    # Values in CFU/100mL or organisms/L
    EPA_DRINKING_WATER_STANDARDS = {
        PathogenType.BACTERIA: {
            "E. coli": 0,  # Zero tolerance
            "Total Coliform": 0,  # Zero tolerance
            "Legionella": 1000,  # Action level
        },
        PathogenType.VIRUS: {
            "Enteroviruses": 1,  # 1 organism/L
            "Norovirus": 1,
            "Hepatitis A": 0,  # Zero tolerance
        },
        PathogenType.PARASITE: {
            "Giardia lamblia": 1,  # 1 organism/L
            "Cryptosporidium": 1,  # 1 organism/L
        },
    }

    # CDC recreational water standards
    CDC_RECREATIONAL_STANDARDS = {
        PathogenType.BACTERIA: {
            "E. coli": 235,  # CFU/100mL
            "Enterococcus": 70,  # CFU/100mL
        },
    }

    # California Title 22 standards for recycled water
    CALIFORNIA_TITLE_22_STANDARDS = {
        PathogenType.BACTERIA: {
            "Total Coliform": 2.2,  # MPN/100mL (7-day median)
            "Total Coliform_max": 23,  # MPN/100mL (single sample)
        },
        PathogenType.VIRUS: {
            "Enteric Virus": 1,  # PFU/40L
        },
        PathogenType.PARASITE: {
            "Giardia/Cryptosporidium": 1,  # Cyst or oocyst/40L
        },
    }

    def check_compliance(
        self,
        pathogen_type: PathogenType,
        pathogen_name: str,
        concentration: float,
        standard: RegulatoryStandard = RegulatoryStandard.EPA_DRINKING_WATER,
        water_type: str = "drinking"
    ) -> Dict:
        """
        Check compliance against regulatory standards.
        
        Args:
            pathogen_type: Type of pathogen
            pathogen_name: Specific pathogen name
            concentration: Measured concentration
            standard: Regulatory standard to check against
            water_type: Type of water (drinking, recreational, recycled)
            
        Returns:
            Compliance assessment dictionary
        """
        # Select appropriate standards
        if standard == RegulatoryStandard.EPA_DRINKING_WATER:
            standards = self.EPA_DRINKING_WATER_STANDARDS
        elif standard == RegulatoryStandard.CDC_RECREATIONAL:
            standards = self.CDC_RECREATIONAL_STANDARDS
        elif standard == RegulatoryStandard.CALIFORNIA_TITLE_22:
            standards = self.CALIFORNIA_TITLE_22_STANDARDS
        else:
            standards = self.EPA_DRINKING_WATER_STANDARDS

        # Get applicable limit
        pathogen_standards = standards.get(pathogen_type, {})
        limit = pathogen_standards.get(pathogen_name)
        
        # If no specific limit, use generic for pathogen type
        if limit is None:
            limit = self._get_generic_limit(pathogen_type, standard)

        # Determine compliance status
        if limit is None:
            status = ComplianceStatus.REQUIRES_REVIEW
            compliant = None
            exceedance = None
        elif concentration == 0:
            status = ComplianceStatus.COMPLIANT
            compliant = True
            exceedance = 0.0
        elif concentration <= limit:
            status = ComplianceStatus.COMPLIANT
            compliant = True
            exceedance = 0.0
        elif limit == 0:
            # Any detection is non-compliant for zero-tolerance standards
            status = ComplianceStatus.NON_COMPLIANT
            compliant = False
            exceedance = float('inf') if concentration > 0 else 0.0
        elif concentration <= limit * 1.2:  # 20% over limit
            status = ComplianceStatus.WARNING
            compliant = False
            exceedance = ((concentration - limit) / limit) * 100
        else:
            status = ComplianceStatus.NON_COMPLIANT
            compliant = False
            exceedance = ((concentration - limit) / limit) * 100

        assessment = {
            "status": status.value,
            "compliant": compliant,
            "pathogen_type": pathogen_type.value,
            "pathogen_name": pathogen_name,
            "concentration": concentration,
            "regulatory_limit": limit,
            "exceedance_percent": round(exceedance, 2) if exceedance is not None else None,
            "standard": standard.value,
            "water_type": water_type,
            "timestamp": datetime.utcnow().isoformat(),
            "actions_required": self._get_required_actions(status, exceedance),
            "reporting_required": status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.WARNING]
        }

        logger.info("compliance_check_completed", **assessment)
        return assessment

    def _get_generic_limit(
        self,
        pathogen_type: PathogenType,
        standard: RegulatoryStandard
    ) -> Optional[float]:
        """Get generic limit for pathogen type when specific pathogen not found."""
        generic_limits = {
            RegulatoryStandard.EPA_DRINKING_WATER: {
                PathogenType.BACTERIA: 0,  # Zero tolerance for unspecified bacteria
                PathogenType.VIRUS: 1,
                PathogenType.PARASITE: 1,
                PathogenType.FUNGUS: 100,
            },
            RegulatoryStandard.CDC_RECREATIONAL: {
                PathogenType.BACTERIA: 235,
            },
        }
        
        return generic_limits.get(standard, {}).get(pathogen_type)

    def _get_required_actions(
        self,
        status: ComplianceStatus,
        exceedance: Optional[float]
    ) -> List[str]:
        """Get required actions based on compliance status."""
        actions = []
        
        if status == ComplianceStatus.NON_COMPLIANT:
            actions.extend([
                "Immediate notification to regulatory authority required",
                "Issue public health advisory",
                "Implement corrective actions",
                "Increase monitoring frequency",
                "Review treatment processes",
                "Restrict water use if necessary"
            ])
        elif status == ComplianceStatus.WARNING:
            actions.extend([
                "Notify management and quality assurance team",
                "Conduct follow-up sampling within 24 hours",
                "Review treatment effectiveness",
                "Document incident and response",
                "Prepare regulatory notification if confirmed"
            ])
        elif status == ComplianceStatus.REQUIRES_REVIEW:
            actions.extend([
                "Consult with regulatory expert",
                "Review applicable standards",
                "Determine appropriate limits",
                "Document review process"
            ])
        else:  # COMPLIANT
            actions.extend([
                "Continue routine monitoring",
                "Document result in compliance records",
                "Maintain current treatment protocols"
            ])
        
        return actions

    def batch_compliance_check(
        self,
        samples: List[Dict],
        standard: RegulatoryStandard = RegulatoryStandard.EPA_DRINKING_WATER
    ) -> Dict:
        """
        Check compliance for multiple samples.
        
        Args:
            samples: List of sample dictionaries with pathogen data
            standard: Regulatory standard to check against
            
        Returns:
            Summary of compliance results
        """
        results = []
        compliant_count = 0
        non_compliant_count = 0
        warning_count = 0
        review_count = 0
        
        for sample in samples:
            result = self.check_compliance(
                pathogen_type=PathogenType(sample['pathogen_type']),
                pathogen_name=sample.get('pathogen_name', 'Unknown'),
                concentration=sample['concentration'],
                standard=standard,
                water_type=sample.get('water_type', 'drinking')
            )
            results.append(result)
            
            if result['status'] == ComplianceStatus.COMPLIANT.value:
                compliant_count += 1
            elif result['status'] == ComplianceStatus.NON_COMPLIANT.value:
                non_compliant_count += 1
            elif result['status'] == ComplianceStatus.WARNING.value:
                warning_count += 1
            else:
                review_count += 1
        
        summary = {
            "total_samples": len(samples),
            "compliant": compliant_count,
            "non_compliant": non_compliant_count,
            "warnings": warning_count,
            "requires_review": review_count,
            "compliance_rate": (compliant_count / len(samples) * 100) if samples else 0,
            "standard": standard.value,
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        }
        
        logger.info("batch_compliance_check_completed", 
                   total=len(samples), compliant=compliant_count, 
                   non_compliant=non_compliant_count)
        
        return summary

    def generate_compliance_report(
        self,
        summary: Dict,
        include_details: bool = True
    ) -> Dict:
        """
        Generate a formatted compliance report.
        
        Args:
            summary: Compliance summary from batch_compliance_check
            include_details: Include detailed results for each sample
            
        Returns:
            Formatted compliance report
        """
        report = {
            "report_type": "regulatory_compliance",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_samples_tested": summary["total_samples"],
                "compliant_samples": summary["compliant"],
                "non_compliant_samples": summary["non_compliant"],
                "warning_samples": summary["warnings"],
                "samples_requiring_review": summary["requires_review"],
                "overall_compliance_rate": f"{summary['compliance_rate']:.2f}%",
                "regulatory_standard": summary["standard"]
            },
            "requires_regulatory_notification": summary["non_compliant"] > 0,
            "overall_status": "PASS" if summary["non_compliant"] == 0 else "FAIL"
        }
        
        if include_details:
            report["detailed_results"] = summary["results"]
        
        return report

