from app.DB.session import sessionLocal
from app.services.page_service import get_or_create_page

db = sessionLocal()
page = get_or_create_page(db, "deepsolv")
print(page.name, page.follower_count, len(page.posts), len(page.employees))
db.close()