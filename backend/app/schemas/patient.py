"""Schemas do paciente (MVP — 3 pacientes fixos, editáveis no localStorage)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MedicationItem(BaseModel):
    name: str = Field(min_length=1, description="Nome do medicamento")
    dose: str = Field(default="", description="Dose (ex: 500mg)")
    frequency: str = Field(default="", description="Frequência (ex: 6/6h)")


class Patient(BaseModel):
    id: str
    name: str
    age: int = Field(ge=0, le=120)
    sex: str = Field(pattern="^[MF]$")
    summary: str = ""
    notes: str = ""
    previous_medications: list[MedicationItem] = Field(default_factory=list)
    has_history: bool = True
