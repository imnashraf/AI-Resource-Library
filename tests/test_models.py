"""Unit tests for ResourceRecord Pydantic models."""

import pytest
from pydantic import ValidationError
from src.catalog.models import ResourceRecord, DifficultyLevel, ContentStatus


def test_valid_resource_record():
    """Verify that valid fields instantiate ResourceRecord correctly."""
    rec = ResourceRecord(
        id="AI-001",
        slug="test-slug",
        title="Test Guide",
        category="Getting Started",
        difficulty=DifficultyLevel.BEGINNER,
        description="A great test guide.",
        source_url="https://aiwithmax.com/guide-test-slug.html",
        status=ContentStatus.WEB_ONLY,
    )
    assert rec.id == "AI-001"
    assert rec.difficulty == DifficultyLevel.BEGINNER
    assert rec.status == ContentStatus.WEB_ONLY
    assert rec.content_type == "Guide"

    csv_dict = rec.to_csv_dict()
    assert csv_dict["ID"] == "AI-001"
    assert csv_dict["Title"] == "Test Guide"
    assert csv_dict["Difficulty"] == "Beginner"


def test_invalid_id_raises_validation_error():
    """Verify that ID not starting with AI- raises ValidationError."""
    with pytest.raises(ValidationError):
        ResourceRecord(
            id="INVALID-001",
            slug="test-slug",
            title="Test Guide",
            category="Getting Started",
            difficulty=DifficultyLevel.BEGINNER,
            description="A great test guide.",
            source_url="https://aiwithmax.com/guide-test-slug.html",
            status=ContentStatus.WEB_ONLY,
        )


def test_invalid_difficulty_raises_validation_error():
    """Verify invalid difficulty string raises ValidationError."""
    with pytest.raises(ValidationError):
        ResourceRecord(
            id="AI-001",
            slug="test-slug",
            title="Test Guide",
            category="Getting Started",
            difficulty="Extreme",  # Invalid
            description="A great test guide.",
            source_url="https://aiwithmax.com/guide-test-slug.html",
            status=ContentStatus.WEB_ONLY,
        )
