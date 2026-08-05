from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import relationship

from app.database import Base


class Subchapter(Base):
    __tablename__ = "subchapters"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id"),
        nullable=False,
        index=True
    )

    subchapter_number = Column(
        Integer,
        nullable=False
    )

    title = Column(
        String,
        nullable=False
    )

    content = Column(
        Text,
        nullable=True
    )

    chapter = relationship(
        "Chapter",
        back_populates="subchapters"
    )