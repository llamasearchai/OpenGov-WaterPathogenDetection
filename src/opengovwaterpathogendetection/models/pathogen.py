"""Pathogen detection data models for water quality monitoring."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class PathogenType(str, Enum):
    """Types of waterborne pathogens."""
    BACTERIA = "bacteria"
    VIRUS = "virus"
    PARASITE = "parasite"
    FUNGUS = "fungus"
    PRION = "prion"


class RiskLevel(str, Enum):
    """Risk levels for pathogen detection."""
    SAFE = "safe"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SampleSource(str, Enum):
    """Water sample source types."""
    DRINKING_WATER = "drinking_water"
    WASTEWATER = "wastewater"
    SURFACE_WATER = "surface_water"
    GROUNDWATER = "groundwater"
    RECREATIONAL_WATER = "recreational_water"
    STORMWATER = "stormwater"


class PathogenBase(BaseModel):
    """Base model for pathogen records."""
    name: str = Field(..., description="Pathogen scientific name")
    common_name: Optional[str] = Field(None, description="Common/colloquial name")
    pathogen_type: PathogenType = Field(..., description="Type of pathogen")
    description: Optional[str] = Field(None, description="Pathogen description and characteristics")
    symptoms: Optional[str] = Field(None, description="Associated health symptoms")
    transmission_route: Optional[str] = Field(None, description="How pathogen spreads")
    incubation_period_days: Optional[int] = Field(None, description="Typical incubation period in days")
    infectious_dose: Optional[str] = Field(None, description="Minimum infectious dose")


class PathogenCreate(PathogenBase):
    """Model for creating a new pathogen record."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Pathogen(PathogenBase):
    """Full pathogen model with metadata."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WaterSampleBase(BaseModel):
    """Base model for water sample records."""
    location: str = Field(..., description="Sample collection location")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    source_type: SampleSource = Field(..., description="Type of water source")
    collection_date: datetime = Field(..., description="When sample was collected")
    temperature_celsius: Optional[float] = Field(None, description="Water temperature in Celsius")
    ph_level: Optional[float] = Field(None, ge=0, le=14, description="pH level of water")
    turbidity_ntu: Optional[float] = Field(None, ge=0, description="Turbidity in NTU")
    dissolved_oxygen_mg_l: Optional[float] = Field(None, ge=0, description="Dissolved oxygen mg/L")
    notes: Optional[str] = Field(None, description="Additional notes")


class WaterSampleCreate(WaterSampleBase):
    """Model for creating a water sample record."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WaterSample(WaterSampleBase):
    """Full water sample model with metadata."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DetectionBase(BaseModel):
    """Base model for pathogen detection records."""
    sample_id: UUID = Field(..., description="Reference to water sample")
    pathogen_id: UUID = Field(..., description="Reference to detected pathogen")
    detected: bool = Field(..., description="Whether pathogen was detected")
    concentration_cfu_ml: Optional[float] = Field(None, ge=0, description="Concentration in CFU/mL")
    concentration_pfu_ml: Optional[float] = Field(None, ge=0, description="Concentration in PFU/mL (for viruses)")
    detection_method: str = Field(..., description="Laboratory detection method used")
    risk_level: RiskLevel = Field(..., description="Assessed risk level")
    exceeds_standard: bool = Field(default=False, description="Exceeds regulatory standards")
    lab_id: Optional[str] = Field(None, description="Laboratory identifier")
    analyzed_by: Optional[str] = Field(None, description="Analyst name/ID")
    notes: Optional[str] = Field(None, description="Additional notes")


class DetectionCreate(DetectionBase):
    """Model for creating a detection record."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Detection(DetectionBase):
    """Full detection model with metadata."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertBase(BaseModel):
    """Base model for pathogen alert records."""
    detection_id: UUID = Field(..., description="Reference to detection that triggered alert")
    alert_type: str = Field(..., description="Type of alert")
    severity: RiskLevel = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    acknowledged: bool = Field(default=False, description="Whether alert has been acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Who acknowledged the alert")
    acknowledged_at: Optional[datetime] = Field(None, description="When alert was acknowledged")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")


class AlertCreate(AlertBase):
    """Model for creating an alert."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Alert(AlertBase):
    """Full alert model with metadata."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MonitoringStationBase(BaseModel):
    """Base model for monitoring station records."""
    name: str = Field(..., description="Station name")
    code: str = Field(..., description="Station code/identifier")
    location: str = Field(..., description="Station location description")
    latitude: float = Field(..., ge=-90, le=90, description="GPS latitude")
    longitude: float = Field(..., ge=-180, le=180, description="GPS longitude")
    source_type: SampleSource = Field(..., description="Type of water monitored")
    active: bool = Field(default=True, description="Whether station is active")
    sampling_frequency_days: Optional[int] = Field(None, ge=1, description="Sampling frequency in days")
    contact_person: Optional[str] = Field(None, description="Contact person")
    contact_email: Optional[str] = Field(None, description="Contact email")
    notes: Optional[str] = Field(None, description="Additional notes")


class MonitoringStationCreate(MonitoringStationBase):
    """Model for creating a monitoring station."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MonitoringStation(MonitoringStationBase):
    """Full monitoring station model with metadata."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PathogenAnalysisResult(BaseModel):
    """Result model for AI-powered pathogen analysis."""
    sample_id: UUID
    overall_risk: RiskLevel
    detected_pathogens: List[str]
    risk_factors: List[str]
    recommendations: List[str]
    compliance_status: str
    analysis_confidence: float = Field(ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
