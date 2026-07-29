from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import relationship

from app.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # One quiz per chapter — the mandatory checkpoint at the end of it.
    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    title = Column(
        String,
        nullable=False
    )

    passing_score = Column(
        Integer,
        nullable=False,
        default=70
    )

    chapter = relationship(
        "Chapter",
        back_populates="quiz"
    )

    questions = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="QuizQuestion.question_number"
    )

    attempts = relationship(
        "QuizAttempt",
        back_populates="quiz",
        cascade="all, delete-orphan"
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    quiz_id = Column(
        Integer,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False
    )

    question_number = Column(
        Integer,
        nullable=False
    )

    question_text = Column(
        Text,
        nullable=False
    )

    quiz = relationship(
        "Quiz",
        back_populates="questions"
    )

    options = relationship(
        "QuizOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuizOption.id"
    )


class QuizOption(Base):
    __tablename__ = "quiz_options"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    question_id = Column(
        Integer,
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False
    )

    option_text = Column(
        String,
        nullable=False
    )

    is_correct = Column(
        Boolean,
        nullable=False,
        default=False
    )

    question = relationship(
        "QuizQuestion",
        back_populates="options"
    )


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    quiz_id = Column(
        Integer,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False
    )

    score = Column(
        Float,
        nullable=False,
        default=0
    )

    passed = Column(
        Boolean,
        nullable=False,
        default=False
    )

    submitted_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    user = relationship("User")

    quiz = relationship(
        "Quiz",
        back_populates="attempts"
    )

    answers = relationship(
        "QuizAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan"
    )


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    attempt_id = Column(
        Integer,
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False
    )

    question_id = Column(
        Integer,
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False
    )

    selected_option_id = Column(
        Integer,
        ForeignKey("quiz_options.id", ondelete="SET NULL"),
        nullable=True
    )

    attempt = relationship(
        "QuizAttempt",
        back_populates="answers"
    )
