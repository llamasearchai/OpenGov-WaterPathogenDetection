"""FastAPI web application for OpenGov-WaterPathogenDetection."""

from contextlib import asynccontextmanager
from typing import List, Optional

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