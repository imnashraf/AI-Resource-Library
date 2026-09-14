"""Domain models and Pydantic schemas for resource cataloging."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class DifficultyLevel(str, Enum):
    """Normalized difficulty classifications."""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    ALL_LEVELS = "Beginner to Advanced"


class ContentStatus(str, Enum):
    """Resource acquisition and access status."""
    DOWNLOADABLE = "DOWNLOADABLE"
    WEB_ONLY = "WEB_ONLY"
    RESTRICTED = "RESTRICTED"
    ERROR = "ERROR"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class ResourceRecord(BaseModel):
    """Complete domain model representing a cataloged AI educational resource."""

    id: str = Field(description="Unique ID, e.g. AI-001")
    slug: str = Field(description="URL slug identifier")
    title: str = Field(description="Official title of the resource")
    category: str = Field(description="Primary topic category")
    subcategory: str = Field(default="General", description="Secondary classification")
    difficulty: DifficultyLevel = Field(description="Skill level")
    description: str = Field(description="Concise description from source")
    source_url: Optional[str] = Field(default="", description="Canonical original URL if available")
    download_url: Optional[str] = Field(default=None, description="Direct download URL if available")
    content_type: str = Field(default="Guide", description="Article, Guide, Cheatsheet, Tool")
    author: str = Field(default="AI Resource Library", description="Author attribution")
    date: Optional[str] = Field(default=None, description="Publication or update date")
    topics: List[str] = Field(default_factory=list, description="Keywords and topic tags")
    ai_tools: List[str] = Field(default_factory=list, description="AI software/models mentioned")
    status: ContentStatus = Field(description="Access and acquisition status")
    local_file: Optional[str] = Field(default=None, description="Relative path to downloaded document")
    local_html: Optional[str] = Field(default=None, description="Relative path to raw cached HTML")
    summary_file: Optional[str] = Field(default=None, description="Relative path to generated summary")
    copyright_status: str = Field(
        default="Public Web / Personal Reference", description="License & reuse status"
    )
    notes: Optional[str] = Field(default="", description="Additional remarks or caveats")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not v.startswith("AI-"):
            raise ValueError(f"Resource ID must start with 'AI-', got: {v}")
        return v

    def to_csv_dict(self) -> dict:
        """Convert record to dictionary matching Master CSV column headers."""
        return {
            "ID": self.id,
            "Title": self.title,
            "Category": self.category,
            "Subcategory": self.subcategory,
            "Difficulty": self.difficulty.value,
            "Description": self.description,
            "Source URL": self.source_url,
            "Download URL": self.download_url or "",
            "Content Type": self.content_type,
            "Author": self.author,
            "Date": self.date or "",
            "Topics": ", ".join(self.topics),
            "AI Tools": ", ".join(self.ai_tools),
            "Status": self.status.value,
            "Local File": self.local_file or "",
            "Copyright/Reuse Status": self.copyright_status,
            "Notes": self.notes or "",
        }
