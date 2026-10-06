from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class AnalysisColumns:
    score: str
    response: Optional[str] = None
    outcome: Optional[str] = None
    encounter_id: Optional[str] = None
    subject_id: Optional[str] = None


@dataclass(frozen=True)
class AnalysisMetadata:
    analysis_id: str
    disease: Optional[str] = None
    population: Optional[str] = None
    care_setting: Optional[str] = None
    intended_user: Optional[str] = None
    intended_use: Optional[str] = None
    data_version: Optional[str] = None
    score_definition: Optional[str] = None
    response_definition: Optional[str] = None
    outcome_definition: Optional[str] = None
    decision_time_definition: Optional[str] = None
    capacity_period: Optional[str] = None


@dataclass(frozen=True)
class Provenance:
    source_type: str
    stakeholders: List[str] = field(default_factory=list)
    date: Optional[str] = None
    citations: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    confidence: str = "low"

