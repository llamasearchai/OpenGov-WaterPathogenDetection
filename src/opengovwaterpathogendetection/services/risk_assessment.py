"""Risk assessment service for pathogen detection."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
import structlog

from ..models.pathogen import PathogenType

logger = structlog.get_logger(__name__)


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Alert type classification."""
    DETECTION = "detection"
    OUTBREAK = "outbreak"
    THRESHOLD = "threshold"
    TREND = "trend"


class RiskAssessmentService:
    """Service for pathogen risk assessment and alerting."""

    # Threshold values for pathogen concentrations (CFU/100mL)
    THRESHOLDS = {
        PathogenType.BACTERIA: {
            RiskLevel.LOW: 100,
            RiskLevel.MEDIUM: 500,
            RiskLevel.HIGH: 1000,
            RiskLevel.CRITICAL: 5000
        },
        PathogenType.VIRUS: {
            RiskLevel.LOW: 10,
            RiskLevel.MEDIUM: 50,
            RiskLevel.HIGH: 100,
            RiskLevel.CRITICAL: 500
        },
        PathogenType.PARASITE: {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 5,
            RiskLevel.HIGH: 10,
            RiskLevel.CRITICAL: 50
        },
        PathogenType.FUNGUS: {
            RiskLevel.LOW: 50,
            RiskLevel.MEDIUM: 200,
            RiskLevel.HIGH: 500,
            RiskLevel.CRITICAL: 1000
        }
    }

    def assess_risk(
        self,
        pathogen_type: PathogenType,
        concentration: float,
        location: str,
        population_exposed: Optional[int] = None
    ) -> Dict:
        """Assess risk level based on pathogen concentration."""
        risk_level = self._calculate_risk_level(pathogen_type, concentration)
        
        # Adjust risk based on population
        if population_exposed and population_exposed > 10000 and risk_level != RiskLevel.LOW:
            risk_level = self._escalate_risk(risk_level)
        
        assessment = {
            "risk_level": risk_level.value,
            "pathogen_type": pathogen_type.value,
            "concentration": concentration,
            "location": location,
            "population_exposed": population_exposed,
            "timestamp": datetime.utcnow().isoformat(),
            "requires_action": risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            "recommendations": self._get_recommendations(risk_level, pathogen_type)
        }
        
        logger.info("risk_assessment_completed", **assessment)
        return assessment

    def _calculate_risk_level(
        self,
        pathogen_type: PathogenType,
        concentration: float
    ) -> RiskLevel:
        """Calculate risk level from concentration."""
        thresholds = self.THRESHOLDS.get(pathogen_type, self.THRESHOLDS[PathogenType.BACTERIA])
        
        if concentration >= thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif concentration >= thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif concentration >= thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _escalate_risk(self, current_risk: RiskLevel) -> RiskLevel:
        """Escalate risk level due to high population exposure."""
        escalation_map = {
            RiskLevel.LOW: RiskLevel.MEDIUM,
            RiskLevel.MEDIUM: RiskLevel.HIGH,
            RiskLevel.HIGH: RiskLevel.CRITICAL,
            RiskLevel.CRITICAL: RiskLevel.CRITICAL
        }
        return escalation_map[current_risk]

    def _get_recommendations(
        self,
        risk_level: RiskLevel,
        pathogen_type: PathogenType
    ) -> List[str]:
        """Get recommendations based on risk level."""
        recommendations = []
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.extend([
                "IMMEDIATE ACTION REQUIRED: Issue public health advisory",
                "Notify all stakeholders and emergency response teams",
                "Implement water treatment interventions immediately",
                "Increase monitoring frequency to daily",
                "Consider water usage restrictions"
            ])
        elif risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "Issue health advisory to at-risk populations",
                "Increase monitoring frequency",
                "Review and enhance treatment processes",
                "Notify regulatory authorities within 24 hours"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "Continue routine monitoring",
                "Review treatment effectiveness",
                "Document findings and trends",
                "Prepare contingency response plans"
            ])
        else:  # LOW
            recommendations.extend([
                "Continue routine surveillance",
                "Maintain standard treatment protocols",
                "Regular reporting to management"
            ])
        
        return recommendations

    def generate_alert(
        self,
        alert_type: AlertType,
        risk_level: RiskLevel,
        details: Dict
    ) -> Dict:
        """Generate an alert based on detection."""
        alert = {
            "alert_id": f"ALERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "alert_type": alert_type.value,
            "risk_level": risk_level.value,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "status": "active",
            "requires_immediate_action": risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        }
        
        logger.warning("alert_generated", **alert)
        return alert

    def analyze_trends(
        self,
        historical_data: List[Dict],
        time_window_days: int = 7
    ) -> Dict:
        """Analyze trends in pathogen detection."""
        if not historical_data:
            return {"trend": "insufficient_data", "alert_required": False}
        
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        recent_data = [
            d for d in historical_data
            if datetime.fromisoformat(d["timestamp"]) > cutoff_date
        ]
        
        if len(recent_data) < 2:
            return {"trend": "insufficient_data", "alert_required": False}
        
        # Calculate trend
        concentrations = [d["concentration"] for d in recent_data]
        avg_concentration = sum(concentrations) / len(concentrations)
        latest_concentration = concentrations[-1]
        
        trend_direction = "increasing" if latest_concentration > avg_concentration * 1.5 else \
                         "decreasing" if latest_concentration < avg_concentration * 0.5 else \
                         "stable"
        
        alert_required = trend_direction == "increasing" and latest_concentration > avg_concentration * 2
        
        return {
            "trend": trend_direction,
            "average_concentration": avg_concentration,
            "latest_concentration": latest_concentration,
            "data_points": len(recent_data),
            "time_window_days": time_window_days,
            "alert_required": alert_required,
            "timestamp": datetime.utcnow().isoformat()
        }
