from playwright.sync_api import sync_playwright

def save_login_session():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.linkedin.com/login")

        print("Log in manually in the browser window, then press Enter here once done.")
        input()

        page.context.storage_state(path="app/scraper/linkedin_saved_session.json")
        print("Session saved.")

        browser.close()

if __name__ == "__main__":
    save_login_session()