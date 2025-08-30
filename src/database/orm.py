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

    #ingredients = relationship("Ingredient", back_populates="user", cascade="all, delete-orphan")
    board = relationship("Board", back_populates="user", cascade="all, delete-orphan")
    board_like = relationship("BoardLike", back_populates="user", cascade="all, delete-orphan")
    board_comment = relationship("BoardComment", back_populates="user", cascade="all, delete-orphan")
"""
class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ingredient_name = Column(String(40), nullable=False)
    category_id = Column(Integer, ForeignKey)
    amount = Column(Integer)
    purchase_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(Enum("active", "inactive", name="status_type"), default="active", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="ingredients")

class IngredientCategory(Base):
    __tablename__ = "ingredients_category"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(40), nullable=False, unique=True)
"""

class Board(Base):
    __tablename__ = "board"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(40), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Boolean, nullable=False, server_default=text("TRUE"))
    like_count = Column(Integer, nullable=False, server_default=text("0"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="board")
    board_like = relationship("BoardLike", back_populates="board")
    board_comment = relationship("BoardComment", back_populates="board")
    board_image = relationship("BoardImage", back_populates="board")

class BoardLike(Base):
    __tablename__ = "board_like"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True)
    board_id = Column(Integer, ForeignKey("board.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="board_like", passive_deletes=True)
    board = relationship("Board", back_populates="board_like", passive_deletes=True)

class BoardComment(Base):
    __tablename__ = "board_comment"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    board_id = Column(Integer, ForeignKey("board.id", ondelete="CASCADE"), nullable=False)
    comment = Column(Text, nullable=False)
    status = Column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="board_comment")
    board = relationship("Board", back_populates="board_comment")

class BoardImage(Base):
    __tablename__ = "board_image"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("board.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(Text, nullable=False)

    board = relationship("Board", back_populates="board_image", passive_deletes=True)