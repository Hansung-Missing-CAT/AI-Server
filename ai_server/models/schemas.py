from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class HealthResponse(BaseModel):
    status: str


class AnalyzeRequest(BaseModel):
    tipId: Optional[str] = None
    imageUrls: List[str] = Field(default_factory=list)
    breedHint: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radiusM: Optional[int] = 2000
    matchCount: Optional[int] = 3


class EmbedRequest(BaseModel):
    petId: str
    imageUrls: List[str] = Field(default_factory=list)
    featureText: Optional[str] = None
    breedHint: Optional[str] = None


class AnalyzeResponse(BaseModel):
    breed: Optional[str]
    confidence: float
    featureText: str
    topMatches: List[Dict[str, Any]]
    diagnostics: Optional[Dict[str, Any]] = None
