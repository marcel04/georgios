from pydantic import BaseModel, ConfigDict


class MenuCategoryResponse(BaseModel):
    """Public category contract; availability and timestamps stay internal."""

    id: int
    name: str
    description: str | None
    display_order: int

    # Read values from SQLAlchemy object attributes instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)
