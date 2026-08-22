from typing import List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    input_text: str = Field(..., description="사용자의 자연어 여행 요구사항")

    @field_validator("input_text")
    @classmethod
    def validate_input_text(cls, v: str) -> str:
        if v is None or v.strip() == "":
            raise ValueError("input_text는 비어 있을 수 없습니다.")
        return v

@dataclass
class TagInfo:
    tag_id: int
    category: str

class TagResult(BaseModel):
    tag_id: int
    category: str
    name: str
    probability: float

class AnalyzeResponse(BaseModel):
    request_id: str
    region: Optional[str] = None
    tags: List[TagResult]
