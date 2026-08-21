import re
from playwright.sync_api import sync_playwright

SESSION_FILE = "app/scraper/linkedin_saved_session.json"


def parse_follower_count(text: str) -> int:
    text = text.lower().replace("followers", "").strip()
    multiplier = 1
    if "k" in text:
        multiplier = 1000
        text = text.replace("k", "")
    elif "m" in text:
        multiplier = 1000000
        text = text.replace("m", "")
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return 0


def get_field_by_label(page, label: str):
    label_el = page.get_by_text(label, exact=True).first
    if not label_el.count():
        return None
    try:
        parent = label_el.locator("xpath=..")
        value = parent.locator("xpath=following-sibling::*[1]").text_content()
        return value.strip() if value else None
    except Exception:
        return None

def scrape_page_info(page):
    data = {
        "page_id": None,
        "url": None,
        "name": None,
        "description": None,
        "website": None,
        "industry": None,
        "headcount": None,
        "specialities": None,
        "follower_count": 0,
        "profile_pic_url": None,
    }

    name_el = page.locator("h1.org-top-card-summary__title").first
    if name_el.count():
        data["name"] = name_el.get_attribute("title")
    if not data["name"]:
        title_text = page.title()
        if title_text:
            data["name"] = title_text.split("|")[0].strip()

    desc_el = page.locator("p.break-words.white-space-pre-wrap").first
    if desc_el.count():
        data["description"] = desc_el.text_content().strip()
    if not data["description"]:
        meta_el = page.locator('meta[name="description"]').first
        if meta_el.count():
            content = meta_el.get_attribute("content")
            data["description"] = content.strip() if content else None

    dts = page.locator("dl.overflow-hidden dt")
    dds = page.locator("dl.overflow-hidden dd")
    for i in range(dts.count()):
        label = dts.nth(i).text_content().strip().lower()
        value = dds.nth(i).text_content().strip()
        if "website" in label:
            data["website"] = value
        elif "industry" in label:
            data["industry"] = value
        elif "company size" in label:
            data["headcount"] = value

    if not data["website"]:
        data["website"] = get_field_by_label(page, "Website")
    if not data["industry"]:
        data["industry"] = get_field_by_label(page, "Industry")
    if not data["headcount"]:
        data["headcount"] = get_field_by_label(page, "Company size")

    data["specialities"] = get_field_by_label(page, "Specialties")

    info_items = page.locator("div.org-top-card-summary-info-list__info-item")
    for i in range(info_items.count()):
        text = info_items.nth(i).text_content().strip()
        if "follower" in text.lower():
            data["follower_count"] = parse_follower_count(text)
    if data["follower_count"] == 0:
        follower_els = page.locator("p, div, span").filter(
            has_text=re.compile(r"[\d.,]+[KM]?\s+followers", re.I)
        )
        if follower_els.count():
            data["follower_count"] = parse_follower_count(follower_els.first.text_content())

    logo_el = page.locator("img.org-top-card-primary-content__logo").first
    if logo_el.count():
        data["profile_pic_url"] = logo_el.get_attribute("src")
    if not data["profile_pic_url"]:
        og_image = page.locator('meta[property="og:image"]').first
        if og_image.count():
            data["profile_pic_url"] = og_image.get_attribute("content")

    return data


def scrape_posts_from_page(page, max_posts: int = 20):
    previous_count = 0
    for _ in range(10):
        articles = page.locator('div[role="article"]')
        current_count = articles.count()
        if current_count >= max_posts or current_count == previous_count:
            break
        previous_count = current_count
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(2000)

    articles = page.locator('div[role="article"]')
    total = min(articles.count(), max_posts)

    posts = []
    for i in range(total):
        article = articles.nth(i)

        more_button = article.locator('button:has-text("more")').first
        if more_button.count():
            try:
                more_button.click(timeout=2000)
                page.wait_for_timeout(300)
            except Exception:
                pass

        content = None
        text_el = article.locator("span.break-words").first
        if text_el.count():
            content = text_el.text_content().strip()

        likes_count = 0
        likes_el = article.locator("span.social-details-social-counts__reactions-count").first
        if likes_el.count():
            likes_text = likes_el.text_content().strip()
            likes_count = parse_follower_count(likes_text + " followers")

        posted_at = None
        time_el = article.locator("span.update-components-actor__sub-description").first
        if time_el.count():
            raw_text = time_el.text_content().strip()
            posted_at = raw_text.split("•")[0].strip()

        post_urn = article.get_attribute("data-urn")
        post_url = f"https://www.linkedin.com/feed/update/{post_urn}" if post_urn else None

        comments = scrape_comments(article, page)

        posts.append({
            "content": content,
            "likes_count": likes_count,
            "posted_at": posted_at,
            "post_url": post_url,
            "comments": comments,
        })

    return posts


def scrape_comments(article, page, max_load_more_clicks: int = 2):
    comments = []

    comment_toggle = article.locator('button[aria-label*="comments on"]').first
    if not comment_toggle.count():
        return comments

    try:
        comment_toggle.click(timeout=3000)
        page.wait_for_timeout(2500)
    except Exception:
        return comments

    for _ in range(max_load_more_clicks):
        load_more = article.locator('button:has-text("Load more comments")').first
        if load_more.count():
            try:
                load_more.click(timeout=2000)
                page.wait_for_timeout(1500)
            except Exception:
                break
        else:
            break

    comment_entities = article.locator("article.comments-comment-entity")
    total = comment_entities.count()

    for i in range(total):
        entity = comment_entities.nth(i)

        more_btn = entity.locator('span:has-text("...more")').first
        if more_btn.count():
            try:
                more_btn.click(timeout=1500)
                page.wait_for_timeout(200)
            except Exception:
                pass

        author_name = None
        author_el = entity.locator("span.comments-comment-meta__description-title").first
        if author_el.count():
            author_name = author_el.text_content().strip()

        content = None
        text_el = entity.locator("span.comments-comment-item__main-content").first
        if text_el.count():
            content = text_el.text_content().strip()

        comments.append({
            "author_name": author_name,
            "content": content,
        })

    return comments



def scrape_people_from_page(page, max_people: int = 20):
    previous_count = 0
    for _ in range(10):
        cards = page.locator("li.org-people-profile-card__profile-card-spacing")
        current_count = cards.count()
        if current_count >= max_people or current_count == previous_count:
            break
        previous_count = current_count

        load_more = page.locator("button.scaffold-finite-scroll__load-button").first
        if load_more.count():
            try:
                load_more.click(timeout=2000)
            except Exception:
                pass
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(2000)

    cards = page.locator("li.org-people-profile-card__profile-card-spacing")
    total = min(cards.count(), max_people)

    people = []
    for i in range(total):
        card = cards.nth(i)

        name = None
        profile_url = None
        name_el = card.locator("a.link-without-visited-state").first
        if name_el.count():
            aria_label = name_el.get_attribute("aria-label")
            if aria_label:
                name = re.sub(r"^View\s+", "", aria_label)
                name = re.sub(r"[’']s profile$", "", name).strip()
            profile_url = name_el.get_attribute("href")

        headline = None
        headline_el = card.locator("div.artdeco-entity-lockup__subtitle").first
        if headline_el.count():
            headline = headline_el.text_content().strip()

        people.append({
            "name": name,
            "profile_url": profile_url,
            "headline": headline,
        })

    return people


def scrape_full_page(page_id: str, max_posts: int = 20, max_people: int = 20):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=SESSION_FILE)
        page = context.new_page()

        about_url = f"https://www.linkedin.com/company/{page_id}/about/"
        page.goto(about_url, timeout=60000)
        page.wait_for_timeout(4000)
        page_info = scrape_page_info(page)
        page_info["page_id"] = page_id
        page_info["url"] = about_url

        posts_url = f"https://www.linkedin.com/company/{page_id}/posts/"
        page.goto(posts_url, timeout=60000)
        page.wait_for_timeout(4000)
        posts = scrape_posts_from_page(page, max_posts)

        people_url = f"https://www.linkedin.com/company/{page_id}/people/"
        page.goto(people_url, timeout=60000)
        page.wait_for_timeout(4000)
        people = scrape_people_from_page(page, max_people)

        browser.close()

    return {
        "page": page_info,
        "posts": posts,
        "people": people,
    }


if __name__ == "__main__":
    result = scrape_full_page("deepsolv", max_posts=5, max_people=5)
    print(result["page"]["name"])
    print(f"Posts scraped: {len(result['posts'])}")
    print(f"People scraped: {len(result['people'])}")