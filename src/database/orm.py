from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum, text, TIMESTAMP, Text, Boolean
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
    expiration_alerts = relationship("ExpirationAlert", back_populates="user", cascade="all, delete-orphan")
    boards = relationship("Board", back_populates="user", cascade="all, delete-orphan")
    board_comments = relationship("BoardComment", back_populates="user", cascade="all, delete-orphan")
    board_likes = relationship("BoardLike", back_populates="user", cascade="all, delete-orphan")
    like_recipe = relationship("LikeRecipe", back_populates="user", cascade="all, delete-orphan")


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
    expiration_alerts = relationship("ExpirationAlert", back_populates="ingredient", cascade="all, delete-orphan")

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

    user = relationship("User", back_populates="expiration_alerts")
    ingredient = relationship("Ingredient", back_populates="expiration_alerts")

class Board(Base):
    __tablename__ = "board"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(40), nullable=False)
    content = Column(Text, nullable=False)
    like_count = Column(Integer, nullable=False, server_default=text("0"))
    status = Column(Boolean, nullable=False, server_default=text("TRUE"))
    exist_image = Column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="boards")
    comments = relationship("BoardComment", back_populates="board", cascade="all, delete-orphan")
    likes = relationship("BoardLike", back_populates="board", cascade="all, delete-orphan")
    images = relationship("BoardImage", back_populates="board", cascade="all, delete-orphan")

class BoardComment(Base):
    __tablename__ = "board_comment"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    board_id = Column(Integer, ForeignKey("board.id", ondelete="CASCADE"), nullable=False)
    comment = Column(Text, nullable=False)
    status = Column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="board_comments")
    board = relationship("Board", back_populates="comments")

class BoardLike(Base):
    __tablename__ = "board_like"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    board_id = Column(Integer, ForeignKey("board.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="board_likes")
    board = relationship("Board", back_populates="likes")

class BoardImage(Base):
    __tablename__ = "board_image"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("board.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    board = relationship("Board", back_populates="images")

class LikeRecipe(Base):
    __tablename__ = "like_recipe"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipe = Column(Text, nullable=False)
    status = Column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="like_recipe")