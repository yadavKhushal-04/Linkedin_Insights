from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.DB.session import get_DB
from app.schemas.page import PageDetailOut
from app.services.page_service import get_or_create_page
from fastapi import Query
from typing import Optional
from app.DB.models import Page
from app.schemas.page import PaginatedPagesOut
from app.DB.models import Post
from app.schemas.page import PaginatedPostsOut
from app.schemas.page import PaginatedPeopleOut


router = APIRouter(prefix="/pages", tags=["Pages"])


@router.get("", response_model=PaginatedPagesOut)
def list_pages(
    db: Session = Depends(get_DB),
    name: Optional[str] = Query(None, description="Search by page name"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    min_followers: Optional[int] = Query(None),
    max_followers: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    query = db.query(Page)

    if name:
        query = query.filter(Page.name.ilike(f"%{name}%"))
    if industry:
        query = query.filter(Page.industry.ilike(f"%{industry}%"))
    if min_followers is not None:
        query = query.filter(Page.follower_count >= min_followers)
    if max_followers is not None:
        query = query.filter(Page.follower_count <= max_followers)

    total = query.count()
    results = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": results,
    }


@router.get("/{page_id}", response_model=PageDetailOut)
def get_page(page_id: str, db: Session = Depends(get_DB)):
    page = get_or_create_page(db, page_id)

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return page


@router.get("/{page_id}/posts", response_model=PaginatedPostsOut)
def get_page_posts(
    page_id: str,
    db: Session = Depends(get_DB),
    skip: int = Query(0, ge=0),
    limit: int = Query(15, ge=1, le=25),
):
    page = db.query(Page).filter(Page.page_id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    query = db.query(Post).filter(Post.page_id == page.id).order_by(Post.id.desc())

    total = query.count()
    results = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": results,
    }


@router.get("/{page_id}/people", response_model=PaginatedPeopleOut)
def get_page_people(
    page_id: str,
    db: Session = Depends(get_DB),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    page = db.query(Page).filter(Page.page_id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    total = len(page.employees)
    results = page.employees[skip: skip + limit]

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": results,
    }