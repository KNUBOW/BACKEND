from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum, text, TIMESTAMP
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
    status = Column(Enum("active", "inactive", name="status_type"), default="active", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)