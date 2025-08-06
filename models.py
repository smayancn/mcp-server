from pydantic import BaseModel
from typing import List, Dict


class MCPStatus(BaseModel):
    cpu_percent: float
    memory_used: float
    memory_total: float
    storage: str

