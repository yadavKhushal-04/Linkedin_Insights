from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.DB.session import get_DB
from app.schemas.page import PageDetailOut
from app.services.page_service import get_or_create_page

router = APIRouter(prefix="/pages", tags=["Pages"])

@router.get("/{page_id}", response_model=PageDetailOut)
def get_page(page_id: str, db: Session = Depends(get_DB)):
    page = get_or_create_page(db, page_id)

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return page