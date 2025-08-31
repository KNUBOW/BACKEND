from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum, text, TIMESTAMP, Text, Boolean, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(128), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    name = Column(String(20), nullable=False)
    nickname = Column(String(50), nullable=False, unique=True)
    birth = Column(Date, nullable=False)
    gender = Column(Enum("male", "female", name="gender_type"), nullable=False)
    phone_num = Column(String(128), unique=True)
    social_auth = Column(Enum("google", "naver", "none", name="social_auth_type"), default="none", nullable=False)
    status = Column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    ingredients = relationship("Ingredient", back_populates="user", cascade="all, delete-orphan")

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ingredient_name = Column(String(40), nullable=False)
    category_id = Column(Integer, ForeignKey("ingredient_category.id", ondelete="CASCADE"), nullable=False)
    purchase_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="ingredients")
    ingredient_category = relationship("IngredientCategory", back_populates="ingredients")

class IngredientCategory(Base):
    __tablename__ = "ingredient_category"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(40), nullable=False)
    expiration_days = Column(Integer, nullable=False)

    ingredients = relationship("Ingredient", back_populates="ingredient_category")

class ExpirationAlert(Base):
    __tablename__ = "expiration_alert"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False)
    days_left = Column(Integer, nullable=False)
    is_read = Column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
