from sqlalchemy.orm import Session
from app.DB.models import Page, Post, Comment, Person
from app.scraper.linkedin_scraper import scrape_full_page


def save_scraped_data(db: Session, scraped: dict) -> Page:
    page_data = scraped["page"]

    new_page = Page(
        linkedin_id=page_data.get("linkedin_id"),
        page_id=page_data["page_id"],
        name=page_data.get("name"),
        url=page_data.get("url"),
        profile_pic_url=page_data.get("profile_pic_url"),
        description=page_data.get("description"),
        website=page_data.get("website"),
        industry=page_data.get("industry"),
        follower_count=page_data.get("follower_count", 0),
        headcount=page_data.get("headcount"),
        specialities=page_data.get("specialities"),
    )
    db.add(new_page)
    db.flush()

    for post_data in scraped["posts"]:
        new_post = Post(
            page_id=new_page.id,
            content=post_data.get("content"),
            post_url=post_data.get("post_url"),
            likes_count=post_data.get("likes_count", 0),
            posted_at=post_data.get("posted_at"),
        )
        db.add(new_post)
        db.flush()

        for comment_data in post_data.get("comments", []):
            new_comment = Comment(
                post_id=new_post.id,
                author_name=comment_data.get("author_name"),
                content=comment_data.get("content"),
            )
            db.add(new_comment)

    for person_data in scraped["people"]:
        existing_person = None
        if person_data.get("profile_url"):
            existing_person = db.query(Person).filter(
                Person.profile_url == person_data["profile_url"]
            ).first()

        if existing_person:
            new_page.employees.append(existing_person)
        else:
            new_person = Person(
                name=person_data.get("name"),
                profile_url=person_data.get("profile_url"),
                headline=person_data.get("headline"),
            )
            db.add(new_person)
            new_page.employees.append(new_person)

    db.commit()
    db.refresh(new_page)
    return new_page


def get_or_create_page(db: Session, page_id: str) -> Page:
    existing = db.query(Page).filter(Page.page_id == page_id).first()
    if existing:
        return existing

    scraped = scrape_full_page(page_id)
    new_page = save_scraped_data(db, scraped)
    return new_page