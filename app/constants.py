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
