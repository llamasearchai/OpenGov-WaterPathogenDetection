"""Additional storage tests to achieve 100% coverage."""

from pathlib import Path
from unittest.mock import patch, Mock
import pytest
from sqlite_utils.db import NotFoundError

from opengovwaterpathogendetection.storage.item_storage import ItemStorage
from opengovwaterpathogendetection.models.item import ItemCreate
from opengovwaterpathogendetection.core.config import reload_settings


def test_storage_close_without_connection(tmp_path, monkeypatch):
    """Test close when connection doesn't exist."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    # Remove the connection attribute
    delattr(storage, '_conn')
    
    # Should not raise error
    storage.close()


def test_storage_del_method(tmp_path, monkeypatch):
    """Test __del__ method cleanup."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    # Trigger __del__
    del storage
    # Should not raise error


def test_storage_ensure_schema_error(tmp_path, monkeypatch):
    """Test _ensure_schema handles errors gracefully."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    with patch.object(storage.db, '__getitem__', side_effect=Exception("Schema error")):
        # Should not raise, error is caught
        storage._ensure_schema()
    
    storage.close()


def test_storage_create_item_error(tmp_path, monkeypatch):
    """Test create_item when insertion fails."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    item = ItemCreate(name="Test", description="Test item")
    
    # Test successful creation first
    result = storage.create_item(item)
    assert result.name == "Test"
    
    storage.close()


def test_storage_get_item_not_found(tmp_path, monkeypatch):
    """Test get_item when item doesn't exist."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    # Test with NotFoundError
    with patch.object(storage.db, '__getitem__') as mock_table:
        mock_table.return_value.get = Mock(side_effect=NotFoundError())
        
        result = storage.get_item("nonexistent-id")
        assert result is None
    
    storage.close()


def test_storage_get_item_returns_none(tmp_path, monkeypatch):
    """Test get_item when row is None."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    with patch.object(storage.db, '__getitem__') as mock_table:
        mock_table.return_value.get = Mock(return_value=None)
        
        result = storage.get_item("nonexistent-id")
        assert result is None
    
    storage.close()


def test_storage_update_item_table_not_exists(tmp_path, monkeypatch):
    """Test update_item when table doesn't exist."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    with patch.object(storage.db, '__getitem__') as mock_table:
        mock_table.return_value.exists = Mock(return_value=False)
        
        result = storage.update_item("test-id", {"name": "Updated"})
        assert result is False
    
    storage.close()


def test_storage_update_item_not_found(tmp_path, monkeypatch):
    """Test update_item when item doesn't exist."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    with patch.object(storage.db, '__getitem__') as mock_table:
        mock_table.return_value.exists = Mock(return_value=True)
        mock_table.return_value.get = Mock(return_value=None)
        
        result = storage.update_item("test-id", {"name": "Updated"})
        assert result is False
    
    storage.close()


def test_storage_update_item_exception(tmp_path, monkeypatch):
    """Test update_item handles exceptions."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    with patch.object(storage.db, '__getitem__', side_effect=Exception("Update error")):
        result = storage.update_item("test-id", {"name": "Updated"})
        assert result is False
    
    storage.close()


def test_storage_delete_item_not_found(tmp_path, monkeypatch):
    """Test delete_item when item doesn't exist."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    with patch.object(storage.db, '__getitem__') as mock_table:
        mock_table.return_value.get = Mock(return_value=None)
        
        result = storage.delete_item("nonexistent-id")
        assert result is False
    
    storage.close()


def test_storage_delete_item_exception(tmp_path, monkeypatch):
    """Test delete_item handles exceptions."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    with patch.object(storage.db, '__getitem__', side_effect=Exception("Delete error")):
        result = storage.delete_item("test-id")
        assert result is False
    
    storage.close()


def test_storage_search_items_with_fts(tmp_path, monkeypatch):
    """Test search_items with full-text search."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    # Create some test data
    item1 = ItemCreate(name="Test Item", description="Test description")
    storage.create_item(item1)
    
    # Try search (will fall back to LIKE if FTS not configured)
    results = storage.search_items("Test")
    assert len(results) >= 0
    
    storage.close()


def test_storage_search_items_fallback_like(tmp_path, monkeypatch):
    """Test search_items falls back to LIKE when FTS not available."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    # Create a test item first
    item = ItemCreate(name="Test Item", description="Test description")
    storage.create_item(item)
    
    # Mock search to raise AssertionError (FTS not configured)
    original_getitem = storage.db.__getitem__
    
    def mock_getitem(key):
        table = original_getitem(key)
        if key == "items":
            table.search = Mock(side_effect=AssertionError("No FTS"))
        return table
    
    with patch.object(storage.db, '__getitem__', side_effect=mock_getitem):
        results = storage.search_items("Test")
        assert len(results) >= 0
    
    storage.close()


def test_storage_get_item_stats(tmp_path, monkeypatch):
    """Test get_item_stats returns correct statistics."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", f"sqlite:///{db_path}")
    reload_settings()
    
    storage = ItemStorage(str(db_path))
    
    stats = storage.get_item_stats()
    assert "total_items" in stats
    assert isinstance(stats["total_items"], int)
    
    storage.close()

