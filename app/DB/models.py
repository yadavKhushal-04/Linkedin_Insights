from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from app.DB.session import Base
from sqlalchemy.orm import relationship
from datetime import datetime

page_employees = Table(
    "page_employees",
    Base.metadata,
    Column("page_id", Integer, ForeignKey("pages.id"), primary_key=True),
    Column("person_id", Integer, ForeignKey("people.id"), primary_key=True),
)


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    linkedin_id = Column(String(255), nullable=True)
    page_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False, index=True)
    url = Column(String(500), nullable=True)
    profile_pic_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True, index=True)
    follower_count = Column(Integer, default=0)
    headcount = Column(String(100), nullable=True)
    specialities = Column(Text, nullable=True)
    last_scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = relationship("Post", back_populates="page", cascade="all, delete-orphan")
    employees = relationship("Person", secondary=page_employees, back_populates="pages")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    content = Column(Text, nullable=True)
    post_url = Column(String(500), nullable=True)
    likes_count = Column(Integer, default=0)
    #linked doesn't provide a timestamp for the post, only a string like 6mo.
    posted_at = Column(String(20), nullable=True)

    page = relationship("Page", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_name = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    commented_at = Column(DateTime, nullable=True)

    post = relationship("Post", back_populates="comments")


class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    linkedin_id = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    profile_url = Column(String(500), nullable=True)
    headline = Column(String(500), nullable=True)

    pages = relationship("Page", secondary=page_employees, back_populates="employees")