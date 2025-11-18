"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Example schemas (you can keep these or remove if not needed)
class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Benefits awareness app schemas
class Benefit(BaseModel):
    """
    Public benefits catalog
    Collection name: "benefit"
    """
    name: str = Field(..., description="Program name")
    agency: Optional[str] = Field(None, description="Administering agency")
    description: str = Field(..., description="What this program provides")
    category: str = Field(..., description="Type e.g., healthcare, food, housing, education")
    url: Optional[str] = Field(None, description="Official info or application link")
    eligibility_notes: Optional[str] = Field(None, description="Human-readable eligibility guidance")

    # Simple eligibility signals used for matching
    min_age: Optional[int] = Field(None, ge=0, le=120)
    max_age: Optional[int] = Field(None, ge=0, le=120)
    max_income: Optional[float] = Field(None, ge=0, description="Upper income bound in USD, optional")
    location: Optional[str] = Field(None, description="State or region code if restricted (e.g., CA, NY)")
    requires_disability: Optional[bool] = Field(None)
    requires_veteran: Optional[bool] = Field(None)
    requires_dependents: Optional[bool] = Field(None, description="True if intended for parents/guardians")
    tags: Optional[List[str]] = Field(default_factory=list, description="Additional matching tags")

class Inquiry(BaseModel):
    """
    Anonymous user profile for matching
    Not stored as a collection by default; used for request validation
    """
    age: Optional[int] = Field(None, ge=0, le=120)
    income: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, description="State/region code, e.g., CA")
    disability: Optional[bool] = None
    veteran: Optional[bool] = None
    dependents: Optional[int] = Field(None, ge=0)
    employment_status: Optional[str] = Field(None)
    housing_status: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(default_factory=list)

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
