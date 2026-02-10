from pydantic import BaseModel, Field
from typing import List, Optional

class SkillItem(BaseModel):
    name: str = Field(..., min_length=1)
    years: Optional[float] = Field(None, ge=0, le=60)

class ExperienceItem(BaseModel):
    company: str = Field(..., min_length=1)
    role: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    highlights: List[str] = []

class CertificationItem(BaseModel):
    name: str
    issuer: Optional[str] = None
    year: Optional[int] = Field(None, ge=1950, le=2100)

class CVExtractResult(BaseModel):
    candidate_name: str = ""
    email: Optional[str] = None
    contact_number: Optional[str] = None
    location: Optional[str] = None
    gap_in_experience: Optional[float] = Field(None, ge=0, le=60)

    overall_years_experience: Optional[float] = Field(None, ge=0, le=60)

    skills: List[SkillItem] = []
    experiences: List[ExperienceItem] = []
    certifications: List[CertificationItem] = []

    ranking_score: float = Field(..., ge=0, le=100)
    ranking_reason: str = ""
