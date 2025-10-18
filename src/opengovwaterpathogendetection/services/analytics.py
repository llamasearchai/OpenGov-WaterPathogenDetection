"""Advanced analytics for pathogen detection and outbreak prediction."""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import structlog

from ..models.pathogen import PathogenType

logger = structlog.get_logger(__name__)


class AnalyticsService:
    """Advanced analytics for water pathogen surveillance."""

    def analyze_temporal_trends(
        self,
        detection_data: List[Dict],
        time_window_days: int = 30,
        threshold_increase: float = 2.0
    ) -> Dict:
        """
        Analyze temporal trends in pathogen detection.
        
        Args:
            detection_data: List of detection records with timestamps and concentrations
            time_window_days: Window for trend analysis
            threshold_increase: Multiplier indicating significant increase
            
        Returns:
            Trend analysis results
        """
        if not detection_data:
            return {"status": "insufficient_data", "trend": "unknown"}

        # Sort by timestamp
        sorted_data = sorted(detection_data, key=lambda x: x['timestamp'])
        
        # Calculate moving averages
        window_size = max(3, time_window_days // 10)  # Smaller window for better sensitivity
        moving_averages = self._calculate_moving_average(sorted_data, window_size)
        
        # Detect trend direction
        if len(moving_averages) < 2:
            # Not enough data for moving averages, use all data
            if len(sorted_data) >= 3:
                concentrations = [d['concentration'] for d in sorted_data]
                early_avg = sum(concentrations[:len(concentrations)//2]) / len(concentrations[:len(concentrations)//2])
                late_avg = sum(concentrations[len(concentrations)//2:]) / len(concentrations[len(concentrations)//2:])
                
                if late_avg > early_avg * threshold_increase:
                    trend = "increasing_significantly"
                elif late_avg > early_avg * 1.2:
                    trend = "increasing"
                elif late_avg < early_avg * 0.5:
                    trend = "decreasing_significantly"
                elif late_avg < early_avg * 0.8:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
        else:
            recent_avg = sum(moving_averages[-3:]) / min(3, len(moving_averages))
            earlier_avg = sum(moving_averages[:3]) / min(3, len(moving_averages))
            
            if recent_avg > earlier_avg * threshold_increase:
                trend = "increasing_significantly"
            elif recent_avg > earlier_avg * 1.2:
                trend = "increasing"
            elif recent_avg < earlier_avg * 0.5:
                trend = "decreasing_significantly"
            elif recent_avg < earlier_avg * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"

        # Calculate statistics
        concentrations = [d['concentration'] for d in sorted_data]
        
        analysis = {
            "trend": trend,
            "time_window_days": time_window_days,
            "total_detections": len(detection_data),
            "average_concentration": sum(concentrations) / len(concentrations),
            "max_concentration": max(concentrations),
            "min_concentration": min(concentrations),
            "moving_averages": moving_averages,
            "alert_level": self._get_trend_alert_level(trend),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("temporal_trend_analysis_completed", trend=trend, 
                   detections=len(detection_data))
        
        return analysis

    def detect_spatial_clusters(
        self,
        location_data: List[Dict],
        cluster_threshold: int = 3
    ) -> Dict:
        """
        Detect geographic clusters of pathogen detections.
        
        Args:
            location_data: List of detections with location information
            cluster_threshold: Minimum detections to identify cluster
            
        Returns:
            Spatial cluster analysis
        """
        # Group by location
        location_counts = defaultdict(list)
        for record in location_data:
            location = record.get('location', 'Unknown')
            location_counts[location].append(record)

        # Identify clusters
        clusters = []
        for location, records in location_counts.items():
            if len(records) >= cluster_threshold:
                concentrations = [r['concentration'] for r in records]
                clusters.append({
                    "location": location,
                    "detection_count": len(records),
                    "average_concentration": sum(concentrations) / len(concentrations),
                    "max_concentration": max(concentrations),
                    "first_detection": min(r['timestamp'] for r in records),
                    "latest_detection": max(r['timestamp'] for r in records),
                    "risk_level": "high" if len(records) >= cluster_threshold * 2 else "medium"
                })

        analysis = {
            "total_locations": len(location_counts),
            "clusters_identified": len(clusters),
            "clusters": sorted(clusters, key=lambda x: x['detection_count'], reverse=True),
            "cluster_threshold": cluster_threshold,
            "requires_investigation": len(clusters) > 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("spatial_cluster_analysis_completed", 
                   clusters=len(clusters), locations=len(location_counts))
        
        return analysis

    def predict_outbreak_risk(
        self,
        recent_detections: List[Dict],
        historical_baseline: Optional[Dict] = None
    ) -> Dict:
        """
        Predict outbreak risk based on detection patterns.
        
        Args:
            recent_detections: Recent pathogen detections
            historical_baseline: Historical baseline data for comparison
            
        Returns:
            Outbreak risk prediction
        """
        if not recent_detections:
            return {"risk_level": "unknown", "confidence": 0}

        # Calculate recent detection rate
        time_span_days = self._calculate_time_span(recent_detections)
        detection_rate = len(recent_detections) / max(time_span_days, 1)
        
        # Calculate average concentration
        avg_concentration = sum(d['concentration'] for d in recent_detections) / len(recent_detections)
        
        # Determine risk factors
        risk_factors = []
        risk_score = 0
        
        # High detection rate
        if detection_rate > 5:  # More than 5 per day
            risk_factors.append("High detection frequency")
            risk_score += 3
        elif detection_rate > 2:
            risk_factors.append("Elevated detection frequency")
            risk_score += 2
        
        # High concentrations
        if avg_concentration > 1000:
            risk_factors.append("Very high pathogen concentrations")
            risk_score += 3
        elif avg_concentration > 500:
            risk_factors.append("High pathogen concentrations")
            risk_score += 2
        
        # Multiple locations
        unique_locations = len(set(d.get('location', 'Unknown') for d in recent_detections))
        if unique_locations > 5:
            risk_factors.append("Wide geographic spread")
            risk_score += 3
        elif unique_locations > 2:
            risk_factors.append("Multiple locations affected")
            risk_score += 2
        
        # Increasing trend
        if len(recent_detections) >= 5:
            sorted_detections = sorted(recent_detections, key=lambda x: x['timestamp'])
            early_avg = sum(d['concentration'] for d in sorted_detections[:len(sorted_detections)//2]) / (len(sorted_detections)//2)
            late_avg = sum(d['concentration'] for d in sorted_detections[len(sorted_detections)//2:]) / (len(sorted_detections) - len(sorted_detections)//2)
            
            if late_avg > early_avg * 2:
                risk_factors.append("Rapidly increasing trend")
                risk_score += 3

        # Determine risk level
        if risk_score >= 8:
            risk_level = "critical"
            confidence = 0.9
        elif risk_score >= 5:
            risk_level = "high"
            confidence = 0.75
        elif risk_score >= 3:
            risk_level = "medium"
            confidence = 0.6
        else:
            risk_level = "low"
            confidence = 0.5

        prediction = {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "confidence": confidence,
            "risk_factors": risk_factors,
            "detection_count": len(recent_detections),
            "detection_rate_per_day": round(detection_rate, 2),
            "average_concentration": round(avg_concentration, 2),
            "unique_locations": unique_locations,
            "time_span_days": time_span_days,
            "recommendation": self._get_outbreak_recommendation(risk_level),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.warning("outbreak_risk_predicted", risk_level=risk_level, 
                      score=risk_score, confidence=confidence)
        
        return prediction

    def generate_summary_statistics(
        self,
        all_data: List[Dict],
        group_by: str = "pathogen_type"
    ) -> Dict:
        """
        Generate comprehensive summary statistics.
        
        Args:
            all_data: All detection data
            group_by: Field to group statistics by
            
        Returns:
            Summary statistics
        """
        if not all_data:
            return {"status": "no_data", "groups": {}}

        # Group data
        groups = defaultdict(list)
        for record in all_data:
            key = record.get(group_by, "Unknown")
            groups[key].append(record)

        # Calculate statistics for each group
        group_stats = {}
        for group_name, records in groups.items():
            concentrations = [r['concentration'] for r in records]
            
            group_stats[group_name] = {
                "count": len(records),
                "average_concentration": round(sum(concentrations) / len(concentrations), 2),
                "median_concentration": round(sorted(concentrations)[len(concentrations)//2], 2),
                "max_concentration": max(concentrations),
                "min_concentration": min(concentrations),
                "std_deviation": round(self._calculate_std_dev(concentrations), 2),
                "unique_locations": len(set(r.get('location', 'Unknown') for r in records))
            }

        summary = {
            "total_records": len(all_data),
            "groups": group_stats,
            "group_by": group_by,
            "most_common_group": max(groups.keys(), key=lambda k: len(groups[k])),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return summary

    def _calculate_moving_average(
        self,
        data: List[Dict],
        window_size: int
    ) -> List[float]:
        """Calculate moving average of concentrations."""
        if len(data) < window_size:
            return [sum(d['concentration'] for d in data) / len(data)]
        
        averages = []
        for i in range(len(data) - window_size + 1):
            window = data[i:i+window_size]
            avg = sum(d['concentration'] for d in window) / window_size
            averages.append(avg)
        
        return averages

    def _calculate_time_span(self, detections: List[Dict]) -> int:
        """Calculate time span in days between first and last detection."""
        if len(detections) < 2:
            return 1
        
        timestamps = [datetime.fromisoformat(d['timestamp']) for d in detections]
        time_span = (max(timestamps) - min(timestamps)).days
        return max(time_span, 1)

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _get_trend_alert_level(self, trend: str) -> str:
        """Get alert level based on trend."""
        if trend in ["increasing_significantly", "outbreak_suspected"]:
            return "critical"
        elif trend == "increasing":
            return "warning"
        elif trend in ["stable", "decreasing"]:
            return "normal"
        else:
            return "unknown"

    def _get_outbreak_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on outbreak risk level."""
        recommendations = {
            "critical": "IMMEDIATE ACTION: Activate emergency response protocol. Notify all stakeholders. Implement control measures.",
            "high": "URGENT: Increase surveillance. Prepare for potential outbreak response. Notify health authorities.",
            "medium": "CAUTION: Monitor situation closely. Review preparedness plans. Consider enhanced surveillance.",
            "low": "ROUTINE: Continue standard monitoring. Maintain current protocols."
        }
        return recommendations.get(risk_level, "Continue monitoring.")

