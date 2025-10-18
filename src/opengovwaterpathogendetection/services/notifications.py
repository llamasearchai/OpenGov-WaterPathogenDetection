"""Notification system for critical alerts and updates."""

from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import structlog

from ..core.config import get_settings

logger = structlog.get_logger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    LOG = "log"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationService:
    """Service for sending notifications and alerts."""

    def __init__(self):
        """Initialize notification service."""
        self.settings = get_settings()
        self.notification_history = []

    def send_alert(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        recipients: Optional[List[str]] = None,
        channels: Optional[List[NotificationChannel]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Send alert notification.
        
        Args:
            title: Alert title
            message: Alert message
            priority: Notification priority
            recipients: List of recipient email addresses
            channels: Delivery channels to use
            metadata: Additional metadata
            
        Returns:
            Notification result
        """
        if channels is None:
            channels = [NotificationChannel.LOG, NotificationChannel.EMAIL]

        notification = {
            "notification_id": f"NOTIF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "message": message,
            "priority": priority.value,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "delivery_results": {}
        }

        # Send via each channel
        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                result = self._send_email(title, message, recipients or [])
                notification["delivery_results"]["email"] = result
            elif channel == NotificationChannel.LOG:
                result = self._log_notification(title, message, priority)
                notification["delivery_results"]["log"] = result
            elif channel == NotificationChannel.WEBHOOK:
                result = self._send_webhook(notification)
                notification["delivery_results"]["webhook"] = result

        # Store in history
        self.notification_history.append(notification)
        
        logger.info("notification_sent", 
                   notification_id=notification["notification_id"],
                   priority=priority.value,
                   channels=len(channels))
        
        return notification

    def send_risk_alert(
        self,
        risk_assessment: Dict,
        recipients: Optional[List[str]] = None
    ) -> Dict:
        """
        Send risk assessment alert.
        
        Args:
            risk_assessment: Risk assessment results
            recipients: Notification recipients
            
        Returns:
            Notification result
        """
        risk_level = risk_assessment.get('risk_level', 'unknown').upper()
        location = risk_assessment.get('location', 'Unknown Location')
        concentration = risk_assessment.get('concentration', 0)
        
        title = f"Risk Alert: {risk_level} - {location}"
        
        message = f"""
Risk Assessment Alert

Risk Level: {risk_level}
Location: {location}
Pathogen Concentration: {concentration} CFU/100mL

{chr(10).join(risk_assessment.get('recommendations', []))}

Timestamp: {risk_assessment.get('timestamp', datetime.utcnow().isoformat())}
"""
        
        priority = self._get_priority_from_risk(risk_level)
        
        return self.send_alert(
            title=title,
            message=message,
            priority=priority,
            recipients=recipients,
            metadata=risk_assessment
        )

    def send_compliance_alert(
        self,
        compliance_result: Dict,
        recipients: Optional[List[str]] = None
    ) -> Dict:
        """
        Send compliance violation alert.
        
        Args:
            compliance_result: Compliance check results
            recipients: Notification recipients
            
        Returns:
            Notification result
        """
        status = compliance_result.get('status', 'unknown').upper()
        pathogen = compliance_result.get('pathogen_name', 'Unknown Pathogen')
        
        title = f"Compliance Alert: {status} - {pathogen}"
        
        message = f"""
Regulatory Compliance Alert

Status: {status}
Pathogen: {pathogen}
Concentration: {compliance_result.get('concentration', 0)}
Regulatory Limit: {compliance_result.get('regulatory_limit', 'N/A')}
Exceedance: {compliance_result.get('exceedance_percent', 0)}%

Required Actions:
{chr(10).join(f"- {action}" for action in compliance_result.get('actions_required', []))}

Standard: {compliance_result.get('standard', 'Unknown')}
Timestamp: {compliance_result.get('timestamp', datetime.utcnow().isoformat())}
"""
        
        priority = NotificationPriority.CRITICAL if status == "NON_COMPLIANT" else NotificationPriority.HIGH
        
        return self.send_alert(
            title=title,
            message=message,
            priority=priority,
            recipients=recipients,
            metadata=compliance_result
        )

    def send_outbreak_alert(
        self,
        outbreak_prediction: Dict,
        recipients: Optional[List[str]] = None
    ) -> Dict:
        """
        Send outbreak prediction alert.
        
        Args:
            outbreak_prediction: Outbreak prediction results
            recipients: Notification recipients
            
        Returns:
            Notification result
        """
        risk_level = outbreak_prediction.get('risk_level', 'unknown').upper()
        confidence = outbreak_prediction.get('confidence', 0) * 100
        
        title = f"Outbreak Risk Alert: {risk_level} Risk Detected"
        
        message = f"""
Outbreak Risk Prediction

Risk Level: {risk_level}
Confidence: {confidence:.0f}%
Risk Score: {outbreak_prediction.get('risk_score', 0)}/12

Risk Factors:
{chr(10).join(f"- {factor}" for factor in outbreak_prediction.get('risk_factors', []))}

Detection Statistics:
- Total Detections: {outbreak_prediction.get('detection_count', 0)}
- Detection Rate: {outbreak_prediction.get('detection_rate_per_day', 0)} per day
- Affected Locations: {outbreak_prediction.get('unique_locations', 0)}
- Average Concentration: {outbreak_prediction.get('average_concentration', 0)} CFU/100mL

Recommendation:
{outbreak_prediction.get('recommendation', 'No recommendation available')}

Timestamp: {outbreak_prediction.get('timestamp', datetime.utcnow().isoformat())}
"""
        
        priority = self._get_priority_from_risk(risk_level)
        
        return self.send_alert(
            title=title,
            message=message,
            priority=priority,
            recipients=recipients,
            metadata=outbreak_prediction
        )

    def get_notification_history(
        self,
        limit: int = 100,
        priority: Optional[NotificationPriority] = None
    ) -> List[Dict]:
        """
        Get notification history.
        
        Args:
            limit: Maximum number of notifications to return
            priority: Filter by priority
            
        Returns:
            List of notifications
        """
        history = self.notification_history
        
        if priority:
            history = [n for n in history if n['priority'] == priority.value]
        
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def _send_email(
        self,
        title: str,
        message: str,
        recipients: List[str]
    ) -> Dict:
        """Send email notification (simulated - requires SMTP configuration)."""
        # In production, this would use actual SMTP configuration
        # For now, we log the email
        
        logger.info("email_notification", 
                   title=title,
                   recipients=len(recipients),
                   message_length=len(message))
        
        return {
            "status": "simulated",
            "recipients": len(recipients),
            "note": "Email sending requires SMTP configuration"
        }

    def _log_notification(
        self,
        title: str,
        message: str,
        priority: NotificationPriority
    ) -> Dict:
        """Log notification."""
        if priority == NotificationPriority.CRITICAL:
            logger.critical("critical_alert", title=title, message=message)
        elif priority == NotificationPriority.HIGH:
            logger.error("high_priority_alert", title=title, message=message)
        elif priority == NotificationPriority.MEDIUM:
            logger.warning("medium_priority_alert", title=title, message=message)
        else:
            logger.info("low_priority_alert", title=title, message=message)
        
        return {"status": "logged", "priority": priority.value}

    def _send_webhook(self, notification: Dict) -> Dict:
        """Send webhook notification (placeholder for future implementation)."""
        logger.info("webhook_notification", notification_id=notification["notification_id"])
        
        return {
            "status": "not_implemented",
            "note": "Webhook integration requires configuration"
        }

    def _get_priority_from_risk(self, risk_level: str) -> NotificationPriority:
        """Convert risk level to notification priority."""
        risk_level = risk_level.lower()
        
        if risk_level == "critical":
            return NotificationPriority.CRITICAL
        elif risk_level == "high":
            return NotificationPriority.HIGH
        elif risk_level == "medium":
            return NotificationPriority.MEDIUM
        else:
            return NotificationPriority.LOW

