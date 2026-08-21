from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CommentOut(BaseModel):
    id: int
    author_name: Optional[str]
    content: Optional[str]

    class Config:
        from_attributes = True


class PostOut(BaseModel):
    id: int
    content: Optional[str]
    post_url: Optional[str]
    likes_count: int
    posted_at: Optional[str]
    comments: List[CommentOut] = []

    class Config:
        from_attributes = True


class PersonOut(BaseModel):
    id: int
    name: str
    profile_url: Optional[str]
    headline: Optional[str]

    class Config:
        from_attributes = True


class PageOut(BaseModel):
    id: int
    page_id: str
    name: str
    url: Optional[str]
    profile_pic_url: Optional[str]
    description: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    follower_count: int
    headcount: Optional[str]
    specialities: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PageDetailOut(PageOut):
    posts: List[PostOut] = []
    employees: List[PersonOut] = []

class PaginatedPagesOut(BaseModel):
    total: int
    skip: int
    limit: int
    results: List[PageOut]

class PaginatedPostsOut(BaseModel):
    total: int
    skip: int
    limit: int
    results: List[PostOut]


class PaginatedPeopleOut(BaseModel):
    total: int
    skip: int
    limit: int
    results: List[PersonOut]