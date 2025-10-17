"""Storage layer for water sample data."""

from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import sqlite3
import structlog
from sqlite_utils import Database

from ..core.config import get_settings

logger = structlog.get_logger(__name__)


class WaterSample:
    """Water sample data model."""
    
    def __init__(
        self,
        sample_id: str,
        location: str,
        collection_date: str,
        collector_name: str,
        sample_type: str,
        temperature: Optional[float] = None,
        ph_level: Optional[float] = None,
        turbidity: Optional[float] = None,
        pathogen_id: Optional[str] = None,
        pathogen_concentration: Optional[float] = None,
        test_date: Optional[str] = None,
        lab_technician: Optional[str] = None,
        notes: Optional[str] = None,
        **kwargs
    ):
        self.sample_id = sample_id
        self.location = location
        self.collection_date = collection_date
        self.collector_name = collector_name
        self.sample_type = sample_type
        self.temperature = temperature
        self.ph_level = ph_level
        self.turbidity = turbidity
        self.pathogen_id = pathogen_id
        self.pathogen_concentration = pathogen_concentration
        self.test_date = test_date
        self.lab_technician = lab_technician
        self.notes = notes


class WaterSampleStorage:
    """Storage operations for water sample records."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize water sample storage."""
        settings = get_settings()
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db = Database(self._conn)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Ensure water samples table exists."""
        try:
            self.db["water_samples"].create({
                "sample_id": str,
                "location": str,
                "collection_date": str,
                "collector_name": str,
                "sample_type": str,
                "temperature": float,
                "ph_level": float,
                "turbidity": float,
                "pathogen_id": str,
                "pathogen_concentration": float,
                "test_date": str,
                "lab_technician": str,
                "notes": str,
                "created_at": str
            }, pk="sample_id", if_not_exists=True)
        except Exception as e:
            logger.error("schema_creation_failed", error=str(e))

    def close(self) -> None:
        """Close database connection."""
        try:
            if getattr(self, "_conn", None):
                self._conn.close()
        except Exception:
            pass

    def __del__(self) -> None:
        """Cleanup on deletion."""
        try:
            self.close()
        except Exception:
            pass

    def create_sample(self, sample_data: Dict) -> WaterSample:
        """Create a new water sample record."""
        try:
            sample_data["created_at"] = datetime.utcnow().isoformat()
            self.db["water_samples"].insert(sample_data)
            logger.info("water_sample_created", sample_id=sample_data["sample_id"])
            return WaterSample(**sample_data)
        except Exception as e:
            logger.error("create_sample_failed", error=str(e))
            raise

    def get_sample(self, sample_id: str) -> Optional[WaterSample]:
        """Get a water sample by ID."""
        try:
            row = self.db["water_samples"].get(sample_id)
            return WaterSample(**dict(row)) if row else None
        except Exception:
            return None

    def list_samples(
        self,
        limit: int = 100,
        offset: int = 0,
        location: Optional[str] = None
    ) -> List[WaterSample]:
        """List water samples with optional filtering."""
        if location:
            rows = self.db.query(
                "SELECT * FROM water_samples WHERE location = ? ORDER BY collection_date DESC LIMIT ? OFFSET ?",
                [location, limit, offset]
            )
        else:
            rows = self.db.query(
                "SELECT * FROM water_samples ORDER BY collection_date DESC LIMIT ? OFFSET ?",
                [limit, offset]
            )
        return [WaterSample(**dict(row)) for row in rows]

    def get_samples_by_pathogen(self, pathogen_id: str) -> List[WaterSample]:
        """Get all samples for a specific pathogen."""
        rows = self.db.query(
            "SELECT * FROM water_samples WHERE pathogen_id = ? ORDER BY test_date DESC",
            [pathogen_id]
        )
        return [WaterSample(**dict(row)) for row in rows]

    def get_samples_by_location(
        self,
        location: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[WaterSample]:
        """Get samples by location and optional date range."""
        if start_date and end_date:
            rows = self.db.query(
                "SELECT * FROM water_samples WHERE location = ? AND collection_date BETWEEN ? AND ? ORDER BY collection_date DESC",
                [location, start_date, end_date]
            )
        else:
            rows = self.db.query(
                "SELECT * FROM water_samples WHERE location = ? ORDER BY collection_date DESC",
                [location]
            )
        return [WaterSample(**dict(row)) for row in rows]

    def get_sample_statistics(self) -> Dict:
        """Get water sample statistics."""
        total_samples = self.db["water_samples"].count
        
        # Get unique locations
        locations = list(self.db.query(
            "SELECT DISTINCT location FROM water_samples"
        ))
        
        # Get samples with pathogen detection
        detected = list(self.db.query(
            "SELECT COUNT(*) as count FROM water_samples WHERE pathogen_id IS NOT NULL"
        ))
        
        return {
            "total_samples": total_samples,
            "unique_locations": len(locations),
            "samples_with_detection": detected[0]["count"] if detected else 0,
            "locations": [loc["location"] for loc in locations]
        }

    def update_sample(self, sample_id: str, updates: Dict) -> bool:
        """Update a water sample record."""
        try:
            existing = self.db["water_samples"].get(sample_id)
            if not existing:
                return False
            self.db["water_samples"].update(sample_id, updates)
            logger.info("water_sample_updated", sample_id=sample_id)
            return True
        except Exception as e:
            logger.error("update_sample_failed", sample_id=sample_id, error=str(e))
            return False

    def delete_sample(self, sample_id: str) -> bool:
        """Delete a water sample record."""
        try:
            existing = self.db["water_samples"].get(sample_id)
            if not existing:
                return False
            self.db["water_samples"].delete(sample_id)
            logger.info("water_sample_deleted", sample_id=sample_id)
            return True
        except Exception as e:
            logger.error("delete_sample_failed", sample_id=sample_id, error=str(e))
            return False
