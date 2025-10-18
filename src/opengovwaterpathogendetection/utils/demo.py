"""Demo data generator and complete workflow demonstration."""

from datetime import datetime, timedelta
import random
from typing import List, Dict
import structlog

from ..models.pathogen import PathogenType, PathogenCreate
from ..storage.pathogen_storage import PathogenStorage
from ..storage.water_sample_storage import WaterSampleStorage
from ..services.risk_assessment import RiskAssessmentService
from ..services.compliance import ComplianceService, RegulatoryStandard
from ..services.analytics import AnalyticsService
from ..services.notifications import NotificationService

logger = structlog.get_logger(__name__)


class DemoDataGenerator:
    """Generate realistic demo data for testing and demonstrations."""
    
    LOCATIONS = [
        "Downtown Treatment Plant",
        "North Reservoir",
        "East Water Tower",
        "South Pumping Station",
        "West Filtration Facility",
        "Central Distribution Hub",
        "River Intake Point",
        "Lake Collection Site"
    ]
    
    PATHOGENS = [
        {
            "id": "ECOLI-001",
            "name": "Escherichia coli",
            "common_name": "E. coli",
            "pathogen_type": "bacteria",
            "description": "Common bacterial indicator of fecal contamination",
            "symptoms": "Diarrhea, abdominal cramps, nausea, vomiting",
            "transmission_route": "Fecal-oral, contaminated water",
            "incubation_period_days": 3,
            "infectious_dose": "10-100 organisms"
        },
        {
            "id": "GIAR-001",
            "name": "Giardia lamblia",
            "common_name": "Giardia",
            "pathogen_type": "parasite",
            "description": "Protozoan parasite causing giardiasis",
            "symptoms": "Chronic diarrhea, weight loss, malabsorption",
            "transmission_route": "Fecal-oral, contaminated water",
            "incubation_period_days": 7,
            "infectious_dose": "10-100 cysts"
        },
        {
            "id": "CRYPTO-001",
            "name": "Cryptosporidium parvum",
            "common_name": "Crypto",
            "pathogen_type": "parasite",
            "description": "Chlorine-resistant waterborne parasite",
            "symptoms": "Watery diarrhea, stomach cramps, fever",
            "transmission_route": "Fecal-oral, recreational water",
            "incubation_period_days": 7,
            "infectious_dose": "10-30 oocysts"
        },
        {
            "id": "LEGION-001",
            "name": "Legionella pneumophila",
            "common_name": "Legionella",
            "pathogen_type": "bacteria",
            "description": "Causes Legionnaires' disease",
            "symptoms": "Pneumonia, high fever, cough, muscle aches",
            "transmission_route": "Inhalation of contaminated water aerosols",
            "incubation_period_days": 10,
            "infectious_dose": "Unknown, varies by strain"
        },
        {
            "id": "NORO-001",
            "name": "Norovirus",
            "common_name": "Stomach flu",
            "pathogen_type": "virus",
            "description": "Highly contagious viral gastroenteritis",
            "symptoms": "Vomiting, diarrhea, stomach pain, nausea",
            "transmission_route": "Fecal-oral, contaminated food/water",
            "incubation_period_days": 1,
            "infectious_dose": "18-2800 viral particles"
        }
    ]
    
    def __init__(self):
        """Initialize demo data generator."""
        self.pathogen_storage = PathogenStorage()
        self.sample_storage = WaterSampleStorage()
    
    def generate_pathogens(self) -> List[str]:
        """Generate demo pathogen records."""
        logger.info("generating_demo_pathogens", count=len(self.PATHOGENS))
        
        pathogen_ids = []
        for pathogen_data in self.PATHOGENS:
            try:
                pathogen = PathogenCreate(**pathogen_data)
                created = self.pathogen_storage.create_pathogen(pathogen)
                pathogen_ids.append(created.id)
                logger.info("pathogen_created", pathogen_id=created.id, name=created.name)
            except Exception as e:
                logger.warning("pathogen_creation_failed", error=str(e), pathogen=pathogen_data["id"])
        
        return pathogen_ids
    
    def generate_water_samples(self, num_samples: int = 50, days_back: int = 30) -> List[str]:
        """Generate realistic water sample data."""
        logger.info("generating_demo_samples", count=num_samples, days_back=days_back)
        
        sample_ids = []
        base_date = datetime.now()
        
        for i in range(num_samples):
            # Random date within the past days_back days
            days_ago = random.randint(0, days_back)
            collection_date = base_date - timedelta(days=days_ago)
            
            # Random location
            location = random.choice(self.LOCATIONS)
            
            # Generate sample data
            sample_id = f"WS-{collection_date.strftime('%Y%m%d')}-{i:03d}"
            
            # Random physical parameters
            temperature = round(random.uniform(15.0, 25.0), 1)
            ph_level = round(random.uniform(6.5, 8.5), 1)
            turbidity = round(random.uniform(0.5, 10.0), 1)
            
            sample_data = {
                "sample_id": sample_id,
                "location": location,
                "collection_date": collection_date.strftime("%Y-%m-%d"),
                "collector_name": random.choice(["John Doe", "Jane Smith", "Bob Johnson", "Alice Williams"]),
                "sample_type": random.choice(["raw_water", "treated_water", "distribution_system"]),
                "temperature": temperature,
                "ph_level": ph_level,
                "turbidity": turbidity
            }
            
            # 30% chance of pathogen detection
            if random.random() < 0.3:
                pathogen_id = random.choice(["ECOLI-001", "GIAR-001", "CRYPTO-001", "LEGION-001", "NORO-001"])
                
                # Generate concentration based on pathogen type
                if pathogen_id == "ECOLI-001":
                    concentration = round(random.uniform(0, 500), 1)
                elif pathogen_id in ["GIAR-001", "CRYPTO-001"]:
                    concentration = round(random.uniform(0, 10), 1)
                elif pathogen_id == "LEGION-001":
                    concentration = round(random.uniform(0, 2000), 1)
                else:  # Norovirus
                    concentration = round(random.uniform(0, 100), 1)
                
                sample_data["pathogen_id"] = pathogen_id
                sample_data["pathogen_concentration"] = concentration
                sample_data["test_date"] = (collection_date + timedelta(days=1)).strftime("%Y-%m-%d")
                sample_data["lab_technician"] = random.choice(["Dr. Sarah Lee", "Dr. Michael Chen", "Dr. Emily Brown"])
            
            try:
                self.sample_storage.create_sample(sample_data)
                sample_ids.append(sample_id)
                logger.info("sample_created", sample_id=sample_id, location=location)
            except Exception as e:
                logger.warning("sample_creation_failed", error=str(e), sample_id=sample_id)
        
        return sample_ids
    
    def close(self):
        """Close storage connections."""
        self.pathogen_storage.close()
        self.sample_storage.close()


class DemoWorkflow:
    """Demonstrate complete system workflows."""
    
    def __init__(self):
        """Initialize demo workflow."""
        self.sample_storage = WaterSampleStorage()
        self.pathogen_storage = PathogenStorage()
        self.risk_service = RiskAssessmentService()
        self.compliance_service = ComplianceService()
        self.analytics_service = AnalyticsService()
        self.notification_service = NotificationService()
    
    def run_complete_demo(self) -> Dict:
        """Run complete demonstration workflow."""
        logger.info("starting_complete_demo")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "workflows": []
        }
        
        # 1. Sample Analysis
        samples = self.sample_storage.list_samples(limit=10)
        results["workflows"].append({
            "name": "Sample Retrieval",
            "status": "success",
            "count": len(samples),
            "message": f"Retrieved {len(samples)} water samples"
        })
        
        # 2. Pathogen Detection
        pathogens = self.pathogen_storage.list_pathogens(limit=10)
        results["workflows"].append({
            "name": "Pathogen Catalog",
            "status": "success",
            "count": len(pathogens),
            "message": f"Found {len(pathogens)} pathogens in database"
        })
        
        # 3. Risk Assessment
        risk_assessments = []
        for sample in samples:
            if hasattr(sample, 'pathogen_concentration') and sample.pathogen_concentration:
                assessment = self.risk_service.assess_risk(
                    pathogen_type=PathogenType.BACTERIA,
                    concentration=sample.pathogen_concentration,
                    location=sample.location,
                    population_exposed=random.randint(1000, 50000)
                )
                risk_assessments.append(assessment)
        
        results["workflows"].append({
            "name": "Risk Assessment",
            "status": "success",
            "count": len(risk_assessments),
            "high_risk_count": sum(1 for r in risk_assessments if r['requires_action']),
            "message": f"Assessed {len(risk_assessments)} detections"
        })
        
        # 4. Compliance Checking
        compliance_checks = []
        for sample in samples:
            if hasattr(sample, 'pathogen_concentration') and sample.pathogen_concentration:
                result = self.compliance_service.check_compliance(
                    pathogen_type=PathogenType.BACTERIA,
                    pathogen_name="E. coli",
                    concentration=sample.pathogen_concentration,
                    standard=RegulatoryStandard.EPA_DRINKING_WATER
                )
                compliance_checks.append(result)
        
        compliant = sum(1 for c in compliance_checks if c.get('compliant'))
        results["workflows"].append({
            "name": "Compliance Checking",
            "status": "success",
            "total": len(compliance_checks),
            "compliant": compliant,
            "non_compliant": len(compliance_checks) - compliant,
            "message": f"Compliance rate: {(compliant/len(compliance_checks)*100) if compliance_checks else 0:.1f}%"
        })
        
        # 5. Outbreak Prediction
        detection_data = []
        for sample in samples:
            if hasattr(sample, 'pathogen_concentration') and sample.pathogen_concentration:
                detection_data.append({
                    "timestamp": sample.collection_date,
                    "concentration": sample.pathogen_concentration,
                    "location": sample.location
                })
        
        if len(detection_data) >= 2:
            prediction = self.analytics_service.predict_outbreak_risk(detection_data)
            results["workflows"].append({
                "name": "Outbreak Prediction",
                "status": "success",
                "risk_level": prediction['risk_level'],
                "confidence": f"{prediction['confidence']*100:.0f}%",
                "message": f"Outbreak risk: {prediction['risk_level']} ({prediction['confidence']*100:.0f}% confidence)"
            })
        
        # 6. Notifications
        if risk_assessments:
            high_risk = [r for r in risk_assessments if r['requires_action']]
            for assessment in high_risk[:3]:  # Send alerts for first 3 high-risk
                self.notification_service.send_risk_alert(assessment)
        
        results["workflows"].append({
            "name": "Notifications",
            "status": "success",
            "alerts_sent": len([r for r in risk_assessments if r['requires_action']]),
            "message": f"Sent alerts for high-risk detections"
        })
        
        logger.info("complete_demo_finished", workflows=len(results["workflows"]))
        return results
    
    def close(self):
        """Close storage connections."""
        self.sample_storage.close()
        self.pathogen_storage.close()

