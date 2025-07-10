from typing import Optional, Dict
from pydantic import BaseModel, Field

class Prompt(BaseModel):
    text: str

class CompositionRequest(BaseModel):
    prompt: Prompt
    format: Optional[str] = Field(default="wav", pattern="^(mp3|aac|wav)$")
    looping: Optional[bool] = False

class CompositionResponse(BaseModel):
    status: str
    task_id: str

class TrackMeta(BaseModel):
    project_id: str
    track_id: str
    prompt: Prompt
    version: int
    track_url: str
    stems_url: Dict[str, str]

class TaskStatus(BaseModel):
    status: str
    meta: Optional[TrackMeta] = None
