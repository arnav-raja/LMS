from enum import Enum


class Department(str, Enum):
    CUSTOMER_RELATIONS = "CR"
    DESIGN = "DE"
    ECOMMERCE = "EC"
    FINANCE = "FI"
    HUMAN_RESOURCES = "HR"
    INVENTORY = "IN"
    MARKETING = "MK"
    OPERATIONS = "OP"
    SALES = "SA"


DEPARTMENT_LABELS = {
    Department.CUSTOMER_RELATIONS: "Customer Relations",
    Department.DESIGN: "Design",
    Department.ECOMMERCE: "E-Commerce",
    Department.FINANCE: "Finance",
    Department.HUMAN_RESOURCES: "Human Resources",
    Department.INVENTORY: "Inventory",
    Department.MARKETING: "Marketing",
    Department.OPERATIONS: "Operations",
    Department.SALES: "Sales",
}


class Seniority(str, Enum):
    MANAGER = "Manager"
    SENIOR = "Senior"
    MID = "Mid"
    JUNIOR = "Junior"


class Role(str, Enum):
    """What an account is allowed to do. There are only two: an admin runs
    the platform, a student consumes it."""
    ADMIN = "admin"
    STUDENT = "student"


class CourseStatus(str, Enum):
    """A course is only visible to students while it is published. Draft
    means still being written; archived means retired without deleting the
    content or anyone's completion history."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


def sql_value_list(enum_class: type[Enum]) -> str:
    """Renders an enum's values as a SQL list for a CHECK constraint, e.g.
    "('admin', 'student')".

    The point is that the constraint and the enum cannot drift apart. These
    value lists were previously written out by hand in both the model and
    the migration, so adding a department meant editing the same list in
    three places and silently breaking writes if you missed one.
    """
    return "(" + ", ".join(f"'{member.value}'" for member in enum_class) + ")"
