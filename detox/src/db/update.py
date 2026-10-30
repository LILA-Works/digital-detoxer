import uuid

from sqlmodel import Field, SQLModel


class Update(SQLModel, table=True):
    __tablename__ = "updates"  # pyright: ignore[reportAssignmentType]

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    message: str
