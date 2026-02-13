from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Any

class SkillItem(BaseModel):
    name: str = Field(..., min_length=1)
    years: Optional[float] = Field(None, ge=0, le=60)

class ExperienceItem(BaseModel):
    company: str = Field(..., min_length=1)
    role: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)

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

    skills: List[SkillItem] = Field(default_factory=list)
    experiences: List[ExperienceItem] = Field(default_factory=list)
    certifications: List[CertificationItem] = Field(default_factory=list)

    ranking_score: float = Field(..., ge=0, le=100)
    ranking_reason: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_ranking(cls, data: Any):
        """
        Accept either:
          - top-level ranking_score/ranking_reason
          - OR rankings[0].resume_ranking_score / resume_ranking_reason
        """
        if not isinstance(data, dict):
            return data

        # Already good
        if data.get("ranking_score") is not None:
            return data

        rankings = data.get("rankings")
        if isinstance(rankings, list) and rankings:
            first = rankings[0]
            if isinstance(first, dict):
                score = first.get("resume_ranking_score") or first.get("ranking_score")
                reason = first.get("resume_ranking_reason") or first.get("ranking_reason")

                if score is not None:
                    data["ranking_score"] = score
                if reason and not data.get("ranking_reason"):
                    data["ranking_reason"] = reason

        return data
