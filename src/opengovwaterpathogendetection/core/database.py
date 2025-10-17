"""Database management for OpenGov-WaterPathogenDetection."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlite_utils import Database
import sqlite3

from ..core.config import get_settings


class DatabaseManager:
    """Manages SQLite database operations for OpenGov-WaterPathogenDetection.

    Provides context manager and explicit close() to ensure connections
    are released promptly, reducing ResourceWarning noise during tests.
    """

    def __init__(self, db_path: Optional[str] = None):
        settings = get_settings()
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db = Database(self._conn)
        self._ensure_schema()

    # --- Resource Management -------------------------------------------------
    def close(self) -> None:
        """Close underlying SQLite connection."""
        try:
            if getattr(self, "_conn", None):
                self._conn.close()
        except Exception:
            pass

    def __enter__(self):  # pragma: no cover - simple context sugar
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover
        self.close()

    def __del__(self):  # pragma: no cover - best effort cleanup
        try:
            self.close()
        except Exception:
            pass

    def _ensure_schema(self) -> None:
        """Ensure core tables exist (idempotent)."""
        try:
            # Legacy items table
            self.db["items"].create({
                "id": str,
                "name": str,
                "description": str,
                "created_at": str,
                "updated_at": str
            }, pk="id", if_not_exists=True)

            # Pathogens table
            self.db["pathogens"].create({
                "id": str,
                "name": str,
                "common_name": str,
                "pathogen_type": str,
                "description": str,
                "symptoms": str,
                "transmission_route": str,
                "incubation_period_days": int,
                "infectious_dose": str,
                "created_at": str,
                "updated_at": str
            }, pk="id", if_not_exists=True)

            # Monitoring stations table
            self.db["monitoring_stations"].create({
                "id": str,
                "name": str,
                "code": str,
                "location": str,
                "latitude": float,
                "longitude": float,
                "source_type": str,
                "active": int,  # SQLite doesn't have boolean
                "sampling_frequency_days": int,
                "contact_person": str,
                "contact_email": str,
                "notes": str,
                "created_at": str,
                "updated_at": str
            }, pk="id", if_not_exists=True)

            # Water samples table
            self.db["water_samples"].create({
                "id": str,
                "location": str,
                "latitude": float,
                "longitude": float,
                "source_type": str,
                "collection_date": str,
                "temperature_celsius": float,
                "ph_level": float,
                "turbidity_ntu": float,
                "dissolved_oxygen_mg_l": float,
                "notes": str,
                "created_at": str,
                "updated_at": str
            }, pk="id", if_not_exists=True)

            # Detections table
            self.db["detections"].create({
                "id": str,
                "sample_id": str,
                "pathogen_id": str,
                "detected": int,  # SQLite boolean as int
                "concentration_cfu_ml": float,
                "concentration_pfu_ml": float,
                "detection_method": str,
                "risk_level": str,
                "exceeds_standard": int,
                "lab_id": str,
                "analyzed_by": str,
                "notes": str,
                "created_at": str,
                "updated_at": str
            }, pk="id", if_not_exists=True)

            # Alerts table
            self.db["alerts"].create({
                "id": str,
                "detection_id": str,
                "alert_type": str,
                "severity": str,
                "title": str,
                "message": str,
                "acknowledged": int,
                "acknowledged_by": str,
                "acknowledged_at": str,
                "resolution_notes": str,
                "created_at": str,
                "updated_at": str
            }, pk="id", if_not_exists=True)

        except Exception:
            pass

    def initialize(self, drop_existing: bool = False) -> None:
        """Initialize the database with schema."""
        if drop_existing:
            # Close existing connection before removing file to avoid read-only state
            try:
                self.close()
            except Exception:
                pass
            if Path(self.db_path).exists():
                Path(self.db_path).unlink()
            # Recreate fresh connection & sqlite-utils wrapper
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.db = Database(self._conn)

        # Ensure schema (idempotent)
        self._ensure_schema()

        print(f"Database initialized at {self.db_path}")

    def seed_sample_data(self) -> None:
        """Seed database with sample data including common waterborne pathogens."""
        from datetime import datetime, timezone
        from uuid import uuid4

        try:
            # Legacy items
            self.db["items"].upsert_all([
                {
                    "id": str(uuid4()),
                    "name": "Sample Item 1",
                    "description": "First sample item",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid4()),
                    "name": "Sample Item 2",
                    "description": "Second sample item",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            ], pk="id")

            # Common waterborne pathogens
            pathogens = [
                {
                    "id": str(uuid4()),
                    "name": "Escherichia coli O157:H7",
                    "common_name": "E. coli O157:H7",
                    "pathogen_type": "bacteria",
                    "description": "Pathogenic strain of E. coli that produces Shiga toxin",
                    "symptoms": "Severe stomach cramps, diarrhea (often bloody), vomiting, fever",
                    "transmission_route": "Fecal-oral, contaminated water or food",
                    "incubation_period_days": 3,
                    "infectious_dose": "10-100 organisms",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid4()),
                    "name": "Cryptosporidium parvum",
                    "common_name": "Crypto",
                    "pathogen_type": "parasite",
                    "description": "Microscopic parasite causing cryptosporidiosis",
                    "symptoms": "Watery diarrhea, stomach cramps, nausea, dehydration",
                    "transmission_route": "Fecal-oral, contaminated water",
                    "incubation_period_days": 7,
                    "infectious_dose": "10-30 oocysts",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid4()),
                    "name": "Giardia lamblia",
                    "common_name": "Giardia",
                    "pathogen_type": "parasite",
                    "description": "Flagellated protozoan parasite causing giardiasis",
                    "symptoms": "Diarrhea, gas, abdominal pain, nausea, weight loss",
                    "transmission_route": "Fecal-oral, contaminated water",
                    "incubation_period_days": 10,
                    "infectious_dose": "10-100 cysts",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid4()),
                    "name": "Legionella pneumophila",
                    "common_name": "Legionella",
                    "pathogen_type": "bacteria",
                    "description": "Bacteria causing Legionnaires' disease",
                    "symptoms": "Cough, shortness of breath, fever, muscle aches, headaches",
                    "transmission_route": "Inhalation of water droplets/aerosols",
                    "incubation_period_days": 7,
                    "infectious_dose": "Variable, depends on host factors",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid4()),
                    "name": "Norovirus",
                    "common_name": "Stomach flu",
                    "pathogen_type": "virus",
                    "description": "Highly contagious virus causing gastroenteritis",
                    "symptoms": "Nausea, vomiting, diarrhea, stomach pain",
                    "transmission_route": "Fecal-oral, contaminated water or food",
                    "incubation_period_days": 1,
                    "infectious_dose": "10-100 viral particles",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid4()),
                    "name": "Hepatitis A virus",
                    "common_name": "Hep A",
                    "pathogen_type": "virus",
                    "description": "Virus causing liver inflammation",
                    "symptoms": "Fatigue, nausea, abdominal pain, jaundice, dark urine",
                    "transmission_route": "Fecal-oral, contaminated water or food",
                    "incubation_period_days": 28,
                    "infectious_dose": "10-100 viral particles",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid4()),
                    "name": "Vibrio cholerae",
                    "common_name": "Cholera",
                    "pathogen_type": "bacteria",
                    "description": "Bacteria causing cholera with severe dehydration",
                    "symptoms": "Profuse watery diarrhea, vomiting, rapid dehydration",
                    "transmission_route": "Fecal-oral, contaminated water",
                    "incubation_period_days": 2,
                    "infectious_dose": "100-1000 organisms",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid4()),
                    "name": "Salmonella typhi",
                    "common_name": "Typhoid fever",
                    "pathogen_type": "bacteria",
                    "description": "Bacteria causing typhoid fever",
                    "symptoms": "High fever, weakness, stomach pains, headache, rash",
                    "transmission_route": "Fecal-oral, contaminated water or food",
                    "incubation_period_days": 14,
                    "infectious_dose": "1000-10000 organisms",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            ]

            self.db["pathogens"].insert_all(pathogens, ignore=True)

            print("Sample data seeded successfully:")
            print(f"  - {len(pathogens)} common waterborne pathogens")

        except Exception as e:  # pragma: no cover - defensive; duplicates etc.
            print(f"Sample data seed note: {e}")

    def migrate(self) -> None:
        """Run database migrations."""
        # Add new columns if needed
        try:
            if "status" not in self.db["items"].columns_dict:
                self.db["items"].add_column("status", str)
                # backfill default
                self.db.execute("UPDATE items SET status = ? WHERE status IS NULL", ["active"])
                print("Database migrations completed")
        except Exception as e:
            print(f"Migration note: {e}")