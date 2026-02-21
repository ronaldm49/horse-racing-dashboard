from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Race(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    name: str
    meeting: str
    start_time: Optional[datetime] = None
    baseline_set_at: Optional[datetime] = None # When baseline was set
    last_bumped_at: Optional[datetime] = Field(default_factory=datetime.utcnow) # New: For sorting
    is_active: bool = Field(default=True)
    result_checked: bool = Field(default=False) # New: Has result been processed?
    winner_name: Optional[str] = None # New: Store winner for record
    next_race_url: Optional[str] = None # New: URL for the next race in the meeting

    runners: List["Runner"] = Relationship(back_populates="race")

class Runner(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    race_id: int = Field(foreign_key="race.id")
    name: str
    number: int = 0 
    silk_url: Optional[str] = None 
    jockey: Optional[str] = None # New: Jockey/Driver name
    current_odds: float
    baseline_odds: Optional[float] = None
    is_d4: bool = False
    status_text: str = "" 
    steam_percentage: float = 0.0 
    is_value: bool = False 
    is_previous_steamer: bool = False # New: Flag if horse was a steamer winner before
    is_non_runner: bool = False # New: Flag if horse is a non-runner
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    race: Race = Relationship(back_populates="runners")

class OddsHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    runner_id: int = Field(foreign_key="runner.id")
    odds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class WinnerHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    horse_name: str = Field(index=True)
    race_date: datetime
    final_odds: float
    steam_percentage: float
    is_steamer: bool = Field(default=False) # True if steam >= 10%
