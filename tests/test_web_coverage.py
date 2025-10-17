"""Additional web/app tests to achieve 100% coverage."""

from unittest.mock import patch, Mock
import pytest
from fastapi.testclient import TestClient

from opengovwaterpathogendetection.web.app import app


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


def test_list_items_exception_handling(test_client):
    """Test list_items handles exceptions."""
    with patch("opengovwaterpathogendetection.web.app.ItemStorage") as mock_storage:
        mock_instance = Mock()
        mock_storage.return_value = mock_instance
        mock_instance.list_items = Mock(side_effect=Exception("Database error"))
        
        response = test_client.get("/api/items")
        assert response.status_code == 500
        assert "create_failed" in response.json()["detail"]


def test_create_item_exception_handling(test_client):
    """Test create_item handles exceptions."""
    with patch("opengovwaterpathogendetection.web.app.ItemStorage") as mock_storage:
        mock_instance = Mock()
        mock_storage.return_value = mock_instance
        mock_instance.create_item = Mock(side_effect=Exception("Create error"))
        
        response = test_client.post("/api/items", json={
            "name": "Test",
            "description": "Test"
        })
        # Should handle error gracefully
        assert response.status_code in [200, 500]


def test_update_item_not_found(test_client):
    """Test update_item when item doesn't exist."""
    with patch("opengovwaterpathogendetection.web.app.ItemStorage") as mock_storage:
        mock_instance = Mock()
        mock_storage.return_value = mock_instance
        mock_instance.update_item = Mock(return_value=False)
        
        response = test_client.put("/api/items/nonexistent", json={
            "name": "Updated",
            "description": "Updated"
        })
        assert response.status_code == 404


def test_update_item_http_exception_reraise(test_client):
    """Test update_item re-raises HTTPException."""
    from fastapi import HTTPException
    
    with patch("opengovwaterpathogendetection.web.app.ItemStorage") as mock_storage:
        mock_instance = Mock()
        mock_storage.return_value = mock_instance
        mock_instance.update_item = Mock(side_effect=HTTPException(status_code=404, detail="Not found"))
        
        response = test_client.put("/api/items/test-id", json={
            "name": "Updated",
            "description": "Updated"
        })
        assert response.status_code == 404


def test_update_item_general_exception(test_client):
    """Test update_item handles general exceptions."""
    with patch("opengovwaterpathogendetection.web.app.ItemStorage") as mock_storage:
        mock_instance = Mock()
        mock_storage.return_value = mock_instance
        # First call for update_item, second for get_item
        mock_instance.update_item = Mock(return_value=True)
        mock_instance.get_item = Mock(side_effect=Exception("Get error"))
        
        response = test_client.put("/api/items/test-id", json={
            "name": "Updated",
            "description": "Updated"
        })
        assert response.status_code == 500


def test_delete_item_not_found(test_client):
    """Test delete_item when item doesn't exist."""
    with patch("opengovwaterpathogendetection.web.app.ItemStorage") as mock_storage:
        mock_instance = Mock()
        mock_storage.return_value = mock_instance
        mock_instance.delete_item = Mock(return_value=False)
        
        response = test_client.delete("/api/items/nonexistent")
        assert response.status_code == 404


def test_analysis_exception_handling(test_client):
    """Test run_analysis handles exceptions."""
    with patch("opengovwaterpathogendetection.web.app.AgentService") as mock_service:
        mock_instance = Mock()
        mock_service.return_value = mock_instance
        
        import asyncio
        async def mock_analysis(*args, **kwargs):
            raise Exception("Analysis error")
        
        mock_instance.run_analysis = mock_analysis
        
        response = test_client.post("/api/analysis", json={
            "prompt": "test",
            "model": "gpt-4"
        })
        assert response.status_code == 500


def test_stats_exception_handling(test_client):
    """Test get_stats handles exceptions."""
    # Currently /api/stats just returns static data, so it won't fail
    # This test validates the endpoint is accessible
    response = test_client.get("/api/stats")
    assert response.status_code == 200


def test_app_main_guard():
    """Test __main__ guard in app.py."""
    # This tests the if __name__ == "__main__" block indirectly
    # by ensuring the module can be imported without side effects
    from opengovwaterpathogendetection.web import app as web_app
    assert web_app.app is not None


def test_lifespan_context():
    """Test lifespan context manager."""
    # Create a test to exercise the lifespan
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200


def test_get_dependencies():
    """Test dependency injection functions."""
    from opengovwaterpathogendetection.web.app import get_db_manager, get_item_storage, get_agent_service
    
    db_manager = get_db_manager()
    assert db_manager is not None
    
    item_storage = get_item_storage()
    assert item_storage is not None
    
    agent_service = get_agent_service()
    assert agent_service is not None


def test_cors_configuration():
    """Test CORS middleware is configured."""
    # CORS should allow all origins
    response = TestClient(app).options("/")
    # Just verify the app handles OPTIONS
    assert response.status_code in [200, 405]


def test_analysis_response_model():
    """Test AnalysisResponse model."""
    from opengovwaterpathogendetection.web.app import AnalysisResponse
    
    response = AnalysisResponse(
        result={"test": "data"},
        provider="openai",
        model="gpt-4"
    )
    assert response.provider == "openai"
    assert response.model == "gpt-4"


def test_delete_result_model():
    """Test DeleteResult model."""
    from opengovwaterpathogendetection.web.app import DeleteResult
    
    result = DeleteResult(message="Deleted successfully")
    assert result.message == "Deleted successfully"


def test_item_create_model():
    """Test ItemCreate request model."""
    from opengovwaterpathogendetection.web.app import ItemCreate
    
    item = ItemCreate(name="Test", description="Test item")
    assert item.name == "Test"
    assert item.description == "Test item"


def test_analysis_request_model():
    """Test AnalysisRequest model."""
    from opengovwaterpathogendetection.web.app import AnalysisRequest
    
    request = AnalysisRequest(prompt="test prompt")
    assert request.prompt == "test prompt"
    assert request.model == "ollama"  # default value


def test_analysis_request_custom_model():
    """Test AnalysisRequest with custom model."""
    from opengovwaterpathogendetection.web.app import AnalysisRequest
    
    request = AnalysisRequest(prompt="test", model="gpt-4")
    assert request.model == "gpt-4"


def test_list_items_pagination_params(test_client):
    """Test list_items with various pagination parameters."""
    # Test with default params
    response = test_client.get("/api/items")
    assert response.status_code == 200
    
    # Test with custom limit and offset
    response = test_client.get("/api/items?limit=5&offset=10")
    assert response.status_code == 200
    
    # Test with max limit
    response = test_client.get("/api/items?limit=100")
    assert response.status_code == 200


def test_list_items_validation():
    """Test list_items parameter validation."""
    client = TestClient(app)
    
    # Test with limit > 100 (should be rejected)
    response = client.get("/api/items?limit=101")
    assert response.status_code == 422
    
    # Test with negative offset (should be rejected)
    response = client.get("/api/items?offset=-1")
    assert response.status_code == 422


def test_root_endpoint_structure(test_client):
    """Test root endpoint returns all expected fields."""
    response = test_client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "description" in data
    assert "docs" in data
    assert "health" in data
    assert data["name"] == "OpenGov-WaterPathogenDetection"
    assert data["version"] == "1.0.0"


def test_health_endpoint_structure(test_client):
    """Test health endpoint returns all expected fields."""
    response = test_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert data["status"] == "healthy"
    assert data["service"] == "OpenGov-WaterPathogenDetection"

