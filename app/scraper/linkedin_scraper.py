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


def scrape_page_basic_info(page_id: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=SESSION_FILE)
        page = context.new_page()

        url = f"https://www.linkedin.com/company/{page_id}/about/"
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)

        data = {
            "page_id": page_id,
            "url": url,
            "name": None,
            "description": None,
            "website": None,
            "industry": None,
            "headcount": None,
            "specialities": None,
            "follower_count": 0,
            "profile_pic_url": None,
        }

        #trying old template first for all the cases , fall back to new template style
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
            elif "specialties" in label:
                data["specialities"] = value


        if not data["website"]:
            data["website"] = get_field_by_label(page, "Website")
        if not data["industry"]:
            data["industry"] = get_field_by_label(page, "Industry")
        if not data["headcount"]:
            data["headcount"] = get_field_by_label(page, "Company size")
        if not data["specialities"]:
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

        browser.close()
        return data




def scrape_posts(page_id: str, max_posts: int = 20):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=SESSION_FILE)
        page = context.new_page()

        url = f"https://www.linkedin.com/company/{page_id}/posts/"
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)

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

            post_urn = article.get_attribute("data-urn")
            post_url = f"https://www.linkedin.com/feed/update/{post_urn}" if post_urn else None


        posted_at = None
        time_el = article.locator("span.update-components-actor__sub-description").first
        if time_el.count():
            raw_text = time_el.text_content().strip()
            posted_at = raw_text.split("•")[0].strip()

            posts.append({
                "content": content,
                "likes_count": likes_count,
                "post_url": post_url,
                "posted_at": posted_at
            })


        browser.close()
        return posts




if __name__ == "__main__":
    # result = scrape_page_basic_info("google")
    # print(result)

    result = scrape_posts("google", max_posts=2)
    for p in result:
            print(p)
            print("---")