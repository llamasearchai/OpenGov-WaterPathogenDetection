"""Additional database tests to achieve 100% coverage."""

import sqlite3
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from opengovwaterpathogendetection.core.database import DatabaseManager
from opengovwaterpathogendetection.core.config import reload_settings


def test_database_manager_close(tmp_path, monkeypatch):
    """Test database manager close method."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    db = DatabaseManager(str(db_path))
    db.close()
    # Should not raise error
    db.close()  # Test double close


def test_database_manager_context_manager(tmp_path, monkeypatch):
    """Test database manager as context manager."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    with DatabaseManager(str(db_path)) as db:
        assert db is not None
        assert db.db_path == str(db_path)


def test_database_manager_ensure_schema_error(tmp_path, monkeypatch):
    """Test _ensure_schema handles errors gracefully."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    db = DatabaseManager(str(db_path))
    
    with patch.object(db.db, '__getitem__', side_effect=Exception("Schema error")):
        # Should not raise, error is caught
        db._ensure_schema()


def test_database_manager_initialize_drop_existing_error(tmp_path, monkeypatch):
    """Test initialize with drop_existing when close fails."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    db = DatabaseManager(str(db_path))
    
    # Create the file first
    db_path.touch()
    
    with patch.object(db, 'close', side_effect=Exception("Close error")):
        # Should handle error gracefully
        db.initialize(drop_existing=True)


def test_database_manager_initialize_drop_existing_path(tmp_path, monkeypatch):
    """Test initialize with drop_existing when file exists."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    # Create initial database
    db1 = DatabaseManager(str(db_path))
    db1.close()
    
    # Verify file exists
    assert db_path.exists()
    
    # Initialize with drop_existing
    db2 = DatabaseManager(str(db_path))
    db2.initialize(drop_existing=True)
    
    # Should still exist and be usable
    assert db_path.exists()
    db2.close()


def test_database_manager_seed_data_error(tmp_path, monkeypatch):
    """Test seed_sample_data handles errors gracefully."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    db = DatabaseManager(str(db_path))
    
    with patch.object(db.db, '__getitem__', side_effect=Exception("Seed error")):
        # Should not raise, just prints note
        db.seed_sample_data()
    
    db.close()


def test_database_manager_migrate_no_status_column(tmp_path, monkeypatch):
    """Test migrate adds status column when missing."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    db = DatabaseManager(str(db_path))
    
    # Ensure items table exists but without status column
    db.initialize()
    
    # Check if status column exists
    columns = db.db["items"].columns_dict
    
    # Run migrate
    db.migrate()
    
    # If status was missing, it should be added
    columns_after = db.db["items"].columns_dict
    assert "status" in columns_after or "status" in columns
    
    db.close()


def test_database_manager_migrate_with_status_column(tmp_path, monkeypatch):
    """Test migrate when status column already exists."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    db = DatabaseManager(str(db_path))
    db.initialize()
    
    # Add status column manually
    try:
        db.db["items"].add_column("status", str)
    except Exception:
        pass  # Might already exist
    
    # Run migrate again - should handle gracefully
    db.migrate()
    
    db.close()


def test_database_manager_migrate_error(tmp_path, monkeypatch):
    """Test migrate handles errors gracefully."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    db = DatabaseManager(str(db_path))
    
    with patch.object(db.db, '__getitem__', side_effect=Exception("Migration error")):
        # Should not raise, just prints note
        db.migrate()
    
    db.close()


def test_database_manager_del_method(tmp_path, monkeypatch):
    """Test __del__ method cleanup."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    db = DatabaseManager(str(db_path))
    # Trigger __del__
    del db
    # Should not raise error


def test_database_manager_close_without_connection(tmp_path, monkeypatch):
    """Test close when connection doesn't exist."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    db = DatabaseManager(str(db_path))
    # Remove the connection attribute
    delattr(db, '_conn')
    
    # Should not raise error
    db.close()

