"""Storage layer for pathogen data."""

from pathlib import Path
from typing import List, Optional
import sqlite3

import structlog
from sqlite_utils import Database
from sqlite_utils.db import NotFoundError

from ..core.config import get_settings
from ..models.pathogen import Pathogen, PathogenCreate, PathogenType

logger = structlog.get_logger(__name__)


class PathogenStorage:
    """Storage operations for pathogen records."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize pathogen storage."""
        settings = get_settings()
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db = Database(self._conn)

    def close(self) -> None:
        """Close underlying SQLite connection."""
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

    def create_pathogen(self, pathogen: PathogenCreate) -> Pathogen:
        """Create a new pathogen record."""
        try:
            pathogen_dict = pathogen.model_dump()
            to_store = {
                "id": str(pathogen_dict["id"]),
                "name": pathogen_dict["name"],
                "common_name": pathogen_dict.get("common_name"),
                "pathogen_type": pathogen_dict["pathogen_type"],
                "description": pathogen_dict.get("description"),
                "symptoms": pathogen_dict.get("symptoms"),
                "transmission_route": pathogen_dict.get("transmission_route"),
                "incubation_period_days": pathogen_dict.get("incubation_period_days"),
                "infectious_dose": pathogen_dict.get("infectious_dose"),
                "created_at": pathogen_dict["created_at"].isoformat(),
                "updated_at": pathogen_dict["updated_at"].isoformat(),
            }
            self.db["pathogens"].insert(to_store)
            return Pathogen(**pathogen_dict)
        except Exception as e:
            logger.error("create_pathogen_failed", error=str(e))
            raise

    def get_pathogen(self, pathogen_id: str) -> Optional[Pathogen]:
        """Get a pathogen by ID."""
        try:
            row = self.db["pathogens"].get(pathogen_id)
            if row:
                return self._row_to_pathogen(row)
            return None
        except NotFoundError:
            return None

    def list_pathogens(
        self,
        limit: int = 100,
        offset: int = 0,
        pathogen_type: Optional[PathogenType] = None
    ) -> List[Pathogen]:
        """List pathogens with optional filtering."""
        if pathogen_type:
            rows = self.db.query(
                "SELECT * FROM pathogens WHERE pathogen_type = ? ORDER BY name LIMIT ? OFFSET ?",
                [pathogen_type.value, limit, offset]
            )
        else:
            rows = self.db.query(
                "SELECT * FROM pathogens ORDER BY name LIMIT ? OFFSET ?",
                [limit, offset]
            )
        return [self._row_to_pathogen(row) for row in rows]

    def search_pathogens(self, query: str) -> List[Pathogen]:
        """Search pathogens by name or symptoms."""
        pattern = f"%{query}%"
        rows = self.db.query(
            "SELECT * FROM pathogens WHERE name LIKE ? OR common_name LIKE ? OR symptoms LIKE ? ORDER BY name",
            [pattern, pattern, pattern]
        )
        return [self._row_to_pathogen(row) for row in rows]

    def update_pathogen(self, pathogen_id: str, updates: dict) -> bool:
        """Update a pathogen record."""
        try:
            table = self.db["pathogens"]
            existing = table.get(pathogen_id)
            if not existing:
                return False
            table.update(pathogen_id, updates)
            return True
        except Exception as e:
            logger.error("update_pathogen_failed", pathogen_id=pathogen_id, error=str(e))
            return False

    def delete_pathogen(self, pathogen_id: str) -> bool:
        """Delete a pathogen record."""
        try:
            table = self.db["pathogens"]
            existing = table.get(pathogen_id)
            if not existing:
                return False
            table.delete(pathogen_id)
            return True
        except Exception as e:
            logger.error("delete_pathogen_failed", pathogen_id=pathogen_id, error=str(e))
            return False

    def get_pathogen_stats(self) -> dict:
        """Get pathogen statistics."""
        total = self.db["pathogens"].count
        by_type = {}
        for row in self.db.query("SELECT pathogen_type, COUNT(*) as count FROM pathogens GROUP BY pathogen_type"):
            by_type[row["pathogen_type"]] = row["count"]

        return {
            "total_pathogens": total,
            "by_type": by_type
        }

    def _row_to_pathogen(self, row: dict) -> Pathogen:
        """Convert database row to Pathogen object."""
        row = dict(row)
        return Pathogen(**row)
