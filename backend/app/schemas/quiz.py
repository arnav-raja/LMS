from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------- admin: build --

class QuizOptionInput(BaseModel):
    # As with chapters, an id means "this is the existing one, edited";
    # null means "new". Options keep their ids so a QuizAnswer that points
    # at one still points at the same answer after the quiz is edited.
    id: int | None = None
    option_text: str
    is_correct: bool = False


class QuizQuestionInput(BaseModel):
    id: int | None = None
    question_text: str
    options: list[QuizOptionInput]


class QuizBuilderRequest(BaseModel):
    title: str
    passing_score: int = 70
    questions: list[QuizQuestionInput]


# ------------------------------------------------------- admin: responses --

class QuizOptionAdminResponse(BaseModel):
    id: int
    option_text: str
    is_correct: bool

    class Config:
        from_attributes = True


class QuizQuestionAdminResponse(BaseModel):
    id: int
    question_number: int
    question_text: str
    options: list[QuizOptionAdminResponse]

    class Config:
        from_attributes = True


class QuizAdminResponse(BaseModel):
    id: int
    chapter_id: int
    title: str
    passing_score: int
    version: int = 1
    questions: list[QuizQuestionAdminResponse]

    class Config:
        from_attributes = True


class AdminQuizListItem(BaseModel):
    """One row in the admin Quizzes page."""
    quiz_id: int
    quiz_title: str
    chapter_id: int
    chapter_title: str
    course_id: int
    course_title: str
    passing_score: int
    version: int = 1
    question_count: int
    attempts_count: int
    pass_count: int


class QuizResultRow(BaseModel):
    user_id: int
    user_name: str
    attempts_count: int
    best_score: float
    passed: bool
    # Lower than the quiz's current version means this result was earned
    # against questions that have since been edited.
    latest_version_attempted: int = 1


class QuizResultsResponse(BaseModel):
    quiz_id: int
    quiz_title: str
    version: int = 1
    rows: list[QuizResultRow]


# --------------------------------------------------------- student: take --

class QuizOptionResponse(BaseModel):
    """No `is_correct` flag — this is what a student sees before answering."""
    id: int
    option_text: str

    class Config:
        from_attributes = True


class QuizQuestionResponse(BaseModel):
    id: int
    question_number: int
    question_text: str
    options: list[QuizOptionResponse]

    class Config:
        from_attributes = True


class QuizTakeResponse(BaseModel):
    id: int
    chapter_id: int
    course_id: int
    title: str
    passing_score: int
    questions: list[QuizQuestionResponse]

    class Config:
        from_attributes = True


class SubmitAnswer(BaseModel):
    question_id: int
    option_id: int | None = None


class SubmitQuizRequest(BaseModel):
    answers: list[SubmitAnswer]


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    score: float
    passed: bool
    submitted_at: datetime
    course_id: int
    certificate_issued: bool = False

    class Config:
        from_attributes = True


class QuizSummary(BaseModel):
    """Embedded in a ChapterResponse so the player knows the quiz's state."""
    id: int
    title: str
    passing_score: int
    is_unlocked: bool
    is_passed: bool
    best_score: float | None = None
    attempts_count: int = 0


class QuizListItem(BaseModel):
    """One row in the student's Quizzes page."""
    quiz_id: int
    quiz_title: str
    chapter_id: int
    chapter_title: str
    course_id: int
    course_title: str
    status: str  # "locked" | "available" | "passed" | "failed"
    best_score: float | None = None
    passing_score: int
    question_count: int
