"""Storage layer for OpenGov-WaterPathogenDetection."""

from pathlib import Path
from typing import List, Optional

import structlog
from sqlite_utils import Database
from sqlite_utils.db import NotFoundError
import sqlite3

from ..core.config import get_settings
from ..models.item import Item, ItemCreate

logger = structlog.get_logger(__name__)


class ItemStorage:
    """Storage operations for OpenGov-WaterPathogenDetection items."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize item storage."""
        settings = get_settings()
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db = Database(self._conn)
        self._ensure_schema()

    def close(self) -> None:
        """Close underlying SQLite connection."""
        try:
            if getattr(self, "_conn", None):
                self._conn.close()
        except Exception:
            pass

    def __del__(self):  # pragma: no cover - best effort cleanup
        try:
            self.close()
        except Exception:
            pass

    def _ensure_schema(self) -> None:
        try:
            self.db["items"].create({
                "id": str,
                "name": str,
                "description": str,
                "created_at": str,
                "updated_at": str
            }, pk="id", if_not_exists=True)
        except Exception:
            pass

    def create_item(self, item: ItemCreate) -> Item:
        """Create a new item."""
        try:
            item_dict = item.model_dump()
            # Persist as strings
            to_store = {
                "id": str(item_dict["id"]),
                "name": item_dict["name"],
                "description": item_dict["description"],
                "created_at": item_dict["created_at"].isoformat(),
                "updated_at": item_dict["updated_at"].isoformat(),
            }
            self.db["items"].insert(to_store)
            # Convert back for domain model (UUID + datetime will parse)
            return Item(**item_dict)
        except Exception as e:
            import traceback
            logger.error("create_item_failed", error=str(e), traceback=traceback.format_exc())
            # Re-raise preserving original exception type for clearer FastAPI error response
            raise

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by ID."""
        try:
            row = self.db["items"].get(item_id)
            logger.debug("storage.get_item.row", item_id=item_id, row=row)
            if row:
                return self._row_to_item(row)
            return None
        except NotFoundError:
            logger.debug("storage.get_item.not_found", item_id=item_id)
            return None

    def list_items(self, limit: int = 100, offset: int = 0) -> List[Item]:
        """List items with pagination.

        Uses explicit SQL for limit/offset because sqlite-utils Table.rows is an iterator
        without built-in pagination parameters.
        """
        rows = self.db.query(
            "SELECT * FROM items ORDER BY created_at LIMIT ? OFFSET ?",
            [limit, offset]
        )
        return [self._row_to_item(row) for row in rows]

    def update_item(self, item_id: str, updates: dict) -> bool:
        """Update an item."""
        updates["updated_at"] = updates.get("updated_at", "2024-01-15T10:00:00")
        try:
            table = self.db["items"]
            # sqlite-utils Table.update(pk, updates) returns None, raising if missing; emulate bool
            if not table.exists():
                return False
            existing = table.get(item_id)
            if not existing:
                return False
            table.update(item_id, updates)
            return True
        except Exception as e:
            logger.error("update_item_failed", item_id=item_id, error=str(e))
            return False

    def delete_item(self, item_id: str) -> bool:
        """Delete an item."""
        try:
            table = self.db["items"]
            existing = table.get(item_id)
            if not existing:
                return False
            table.delete(item_id)
            return True
        except Exception as e:
            logger.error("delete_item_failed", item_id=item_id, error=str(e))
            return False

    def search_items(self, query: str) -> List[Item]:
        """Search items.

        If full-text search is not configured, falls back to a LIKE-based search on
        name and description columns.
        """
        try:
            rows = self.db["items"].search(query)
            return [self._row_to_item(row) for row in rows]
        except AssertionError:
            pattern = f"%{query}%"
            rows = self.db.query(
                "SELECT * FROM items WHERE name LIKE ? OR description LIKE ?",
                [pattern, pattern]
            )
            return [self._row_to_item(row) for row in rows]

    def get_item_stats(self) -> dict:
        """Get item statistics."""
        total_items = self.db["items"].count
        return {
            "total_items": total_items
        }

    def _row_to_item(self, row: dict) -> Item:
        """Convert database row to Item object."""
        row = dict(row)
        row["created_at"] = row["created_at"]
        row["updated_at"] = row["updated_at"]
        logger.debug("storage.row_to_item", row=row)
        return Item(**row)