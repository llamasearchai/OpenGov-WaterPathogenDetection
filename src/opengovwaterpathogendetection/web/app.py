"""FastAPI web application for OpenGov-WaterPathogenDetection."""

from contextlib import asynccontextmanager
from typing import List, Optional, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from ..models.item import Item as DomainItem, ItemCreate as DomainItemCreate

from ..core.config import get_settings
from ..core.database import DatabaseManager
from ..services.agent_service import AgentService
from ..storage.item_storage import ItemStorage


# Local thin request model (reuse domain create for shape where possible)
class ItemCreate(BaseModel):
    name: str
    description: str

class AnalysisRequest(BaseModel):
    prompt: str
    model: str = "ollama"

class AnalysisResponse(BaseModel):
    result: dict
    provider: str
    model: str


# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Future: initialize structured logging, metrics, warm caches, etc.
    yield
    # Future: graceful resource cleanup

app = FastAPI(
    title="OpenGov-WaterPathogenDetection API",
    description="Domain-specific API for water pathogen detection management",
    version="1.0.0",
    lifespan=lifespan
)

# NOTE: Removed broad debug exception handler used during test stabilization.
# A structured handler (logging + correlation id) can be reintroduced later if needed.

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
def get_db_manager():
    return DatabaseManager()

def get_item_storage():
    return ItemStorage()

def get_agent_service():
    return AgentService()

def get_pathogen_storage():
    from ..storage.pathogen_storage import PathogenStorage
    return PathogenStorage()

def get_water_sample_storage():
    from ..storage.water_sample_storage import WaterSampleStorage
    return WaterSampleStorage()


# Routes

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OpenGov-WaterPathogenDetection",
        "version": "1.0.0",
        "description": "Domain-specific API for water pathogen detection management",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "OpenGov-WaterPathogenDetection",
        "version": "1.0.0"
    }

@app.get("/api/items", response_model=List[DomainItem])
async def list_items(
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    storage: ItemStorage = Depends(get_item_storage)
):
    """List items with pagination."""
    try:
        items = storage.list_items(limit=limit, offset=offset)
        return items
    except Exception as e:
        # Bubble up a clearer error for tests (in production we might map codes)
        raise HTTPException(status_code=500, detail=f"create_failed: {e}")

@app.post("/api/items", response_model=DomainItem)
async def create_item(
    item: ItemCreate,
    storage: ItemStorage = Depends(get_item_storage)
):
    """Create a new item."""
    try:
        domain_create = DomainItemCreate(name=item.name, description=item.description)
        created = storage.create_item(domain_create)
        return created
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"create_item_failed: {e}")

@app.get("/api/items/{item_id}", response_model=DomainItem)
async def get_item(
    item_id: str,
    storage: ItemStorage = Depends(get_item_storage)
):
    """Get a specific item by ID."""
    item = storage.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/api/items/{item_id}", response_model=DomainItem)
async def update_item(
    item_id: str,
    item_update: ItemCreate,
    storage: ItemStorage = Depends(get_item_storage)
):
    """Update an existing item."""
    try:
        updates = {
            "name": item_update.name,
            "description": item_update.description,
            "updated_at": "2024-01-15T10:00:00"
        }
        updated = storage.update_item(item_id, updates)
        if not updated:
            raise HTTPException(status_code=404, detail="Item not found")
        return storage.get_item(item_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DeleteResult(BaseModel):
    message: str

@app.delete("/api/items/{item_id}", response_model=DeleteResult)
async def delete_item(
    item_id: str,
    storage: ItemStorage = Depends(get_item_storage)
):
    """Delete an item."""
    deleted = storage.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return DeleteResult(message="Item deleted successfully")

@app.post("/api/analysis", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Run AI analysis on given prompt."""
    try:
        import asyncio
        result = await agent_service.run_analysis(
            request.prompt,
            model=request.model
        )
        return AnalysisResponse(
            result=result,
            provider=result.get("provider", "unknown"),
            model=result.get("model", request.model)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pathogens")
async def list_pathogens(
    limit: int = Query(20, ge=1, le=100, description="Number of pathogens to return"),
    offset: int = Query(0, ge=0, description="Number of pathogens to skip"),
    pathogen_type: Optional[str] = Query(None, description="Filter by type (bacteria/virus/parasite)"),
    storage=Depends(get_pathogen_storage)
):
    """List all pathogens with optional filtering."""
    try:
        from ..models.pathogen import PathogenType
        pt = PathogenType(pathogen_type) if pathogen_type else None
        pathogens = storage.list_pathogens(limit=limit, offset=offset, pathogen_type=pt)
        return [p.model_dump() for p in pathogens]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@app.get("/api/pathogens/{pathogen_id}")
async def get_pathogen(
    pathogen_id: str,
    storage=Depends(get_pathogen_storage)
):
    """Get a specific pathogen by ID."""
    try:
        pathogen = storage.get_pathogen(pathogen_id)
        if not pathogen:
            raise HTTPException(status_code=404, detail="Pathogen not found")
        return pathogen.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@app.get("/api/pathogens/search/{query}")
async def search_pathogens(
    query: str,
    storage=Depends(get_pathogen_storage)
):
    """Search pathogens by name or symptoms."""
    try:
        pathogens = storage.search_pathogens(query)
        return [p.model_dump() for p in pathogens]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@app.get("/api/pathogen-stats")
async def get_pathogen_stats(
    storage=Depends(get_pathogen_storage)
):
    """Get pathogen database statistics."""
    try:
        stats = storage.get_pathogen_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@app.post("/api/water-samples")
async def create_water_sample(
    sample: dict,
    storage=Depends(get_water_sample_storage)
):
    """Create a new water sample record."""
    try:
        from ..models.pathogen import WaterSampleCreate, SampleSource
        from datetime import datetime, timezone

        # Convert dict to WaterSampleCreate model
        sample_create = WaterSampleCreate(
            location=sample["location"],
            latitude=sample.get("latitude"),
            longitude=sample.get("longitude"),
            source_type=SampleSource(sample["source_type"]),
            collection_date=datetime.fromisoformat(sample["collection_date"]) if "collection_date" in sample else datetime.now(timezone.utc),
            temperature_celsius=sample.get("temperature_celsius"),
            ph_level=sample.get("ph_level"),
            turbidity_ntu=sample.get("turbidity_ntu"),
            dissolved_oxygen_mg_l=sample.get("dissolved_oxygen_mg_l"),
            notes=sample.get("notes")
        )
        created = storage.create_sample(sample_create)
        return created.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"create_water_sample_failed: {e}")
    finally:
        storage.close()


@app.get("/api/water-samples")
async def list_water_samples(
    limit: int = Query(20, ge=1, le=100, description="Number of samples to return"),
    offset: int = Query(0, ge=0, description="Number of samples to skip"),
    source_type: Optional[str] = Query(None, description="Filter by source type (drinking_water/wastewater/etc)"),
    location: Optional[str] = Query(None, description="Filter by location"),
    storage=Depends(get_water_sample_storage)
):
    """List water samples with optional filtering."""
    try:
        from ..models.pathogen import SampleSource
        st = SampleSource(source_type) if source_type else None
        samples = storage.list_samples(limit=limit, offset=offset, source_type=st, location=location)
        return [s.model_dump() for s in samples]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@app.get("/api/water-samples/{sample_id}")
async def get_water_sample(
    sample_id: str,
    storage=Depends(get_water_sample_storage)
):
    """Get a specific water sample by ID."""
    try:
        sample = storage.get_sample(sample_id)
        if not sample:
            raise HTTPException(status_code=404, detail="Water sample not found")
        return sample.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@app.get("/api/water-sample-stats")
async def get_water_sample_stats(
    storage=Depends(get_water_sample_storage)
):
    """Get water sample statistics."""
    try:
        stats = storage.get_sample_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@app.get("/api/water-samples/search/{query}")
async def search_water_samples(
    query: str,
    storage=Depends(get_water_sample_storage)
):
    """Search water samples by location or notes."""
    try:
        samples = storage.search_samples(query)
        return [s.model_dump() for s in samples]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@app.get("/api/stats")
async def get_stats(
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get database and system statistics."""
    try:
        # This would need to be implemented based on specific domain
        return {
            "service": "OpenGov-WaterPathogenDetection",
            "version": "1.0.0",
            "items_count": 0,
            "last_updated": "2024-01-15T10:00:00"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compliance/check")
async def check_compliance_endpoint(
    pathogen_type: str,
    pathogen_name: str,
    concentration: float,
    standard: str = "epa_drinking_water"
):
    """Check regulatory compliance for pathogen detection."""
    try:
        from ..services.compliance import ComplianceService, RegulatoryStandard
        from ..models.pathogen import PathogenType
        
        service = ComplianceService()
        result = service.check_compliance(
            pathogen_type=PathogenType(pathogen_type),
            pathogen_name=pathogen_name,
            concentration=concentration,
            standard=RegulatoryStandard(standard)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytics/trends")
async def analyze_trends_endpoint(
    detection_data: List[Dict],
    time_window_days: int = 30
):
    """Analyze temporal trends in pathogen detection."""
    try:
        from ..services.analytics import AnalyticsService
        
        service = AnalyticsService()
        analysis = service.analyze_temporal_trends(detection_data, time_window_days)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytics/outbreak-risk")
async def predict_outbreak_endpoint(
    recent_detections: List[Dict]
):
    """Predict outbreak risk based on recent detections."""
    try:
        from ..services.analytics import AnalyticsService
        
        service = AnalyticsService()
        prediction = service.predict_outbreak_risk(recent_detections)
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notifications/alert")
async def send_alert_endpoint(
    title: str,
    message: str,
    priority: str = "medium",
    recipients: Optional[List[str]] = None
):
    """Send notification alert."""
    try:
        from ..services.notifications import NotificationService, NotificationPriority
        
        service = NotificationService()
        result = service.send_alert(
            title=title,
            message=message,
            priority=NotificationPriority(priority),
            recipients=recipients or []
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/samples")
async def list_water_samples(
    limit: int = Query(100, ge=1, le=1000),
    location: Optional[str] = None
):
    """List water samples."""
    try:
        from ..storage.water_sample_storage import WaterSampleStorage
        
        storage = WaterSampleStorage()
        samples = storage.list_samples(limit=limit, location=location)
        result = [{"sample_id": s.sample_id, "location": s.location, 
                   "collection_date": s.collection_date, "sample_type": s.sample_type,
                   "temperature": s.temperature, "ph_level": s.ph_level}
                  for s in samples]
        storage.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Development server
if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )