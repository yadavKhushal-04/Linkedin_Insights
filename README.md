# LinkedIn Insights Microservice

A backend service that scrapes a given LinkedIn company page and stores its details, posts, comments, and employees in a database, exposing them through a REST API.

## What it does

Give it a LinkedIn company page ID (the last part of the page URL, e.g. `deepsolv` from `linkedin.com/company/deepsolv`) and it will:

- Scrape the page's basic info (name, description, website, industry, follower count, headcount, etc.)
- Scrape its recent posts, along with likes and comments on each post
- Scrape the people listed as working there
- Store all of this in MySQL with proper relationships between Page, Post, Comment, and Person
- Serve it back through a set of REST endpoints, with filtering and pagination

If a page is already in the database, it's served straight from there. If not, it's scraped in real time, saved, and then returned.

## Tech stack

- **FastAPI** – web framework
- **MySQL** + **SQLAlchemy** – database and ORM
- **Alembic** – database migrations
- **Playwright** – browser automation for scraping
- **Pydantic** – request/response validation

## Project structure

```
app/
  main.py                  # FastAPI app entrypoint
  core/config.py            # env config
  DB/
    session.py               # DB engine, session, Base
    models.py                 # SQLAlchemy models
  scraper/
    linkedin_scraper.py       # all scraping logic
    save_session.py            # one-time login script
  services/
    page_service.py           # DB save / get-or-create logic
  schemas/
    page.py                    # Pydantic response schemas
  api/routes/
    pages.py                   # API endpoints
alembic/                     # migrations
postman_collection.json       # exported Postman collection
```

## Setup

### 1. Prerequisites

- Python 3.10+
- MySQL running locally

### 2. Clone and set up a virtual environment

```bash
git clone https://github.com/yadavKhushal-04/Linkedin_Insights
cd LINKEDIN INSIGHTS
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
playwright install chromium
```

### 3. Create the database

```sql
CREATE DATABASE linkedin_insights;
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```
DB_URL=mysql+pymysql://root:yourpassword@localhost:3306/linkedin_insights
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Set up a LinkedIn session

The scraper needs a logged-in session to access most page data. Run this once:

```bash
python app/scraper/save_session.py
```

A browser window will open — log in manually with a LinkedIn account (see note below on why we recommend a secondary account), then press Enter in the terminal once you're on your feed. This saves a session file that the scraper reuses for all future requests, so you don't need to log in again.

### 7. Run the server

```bash
uvicorn app.main:app --reload
```

API docs are available at `http://127.0.0.1:8000/docs`.

## Database schema

![ER Diagram](docs/Linkedin_Insights_ERD.png)

`Page` has a one-to-many relationship with `Post`, which has a one-to-many relationship with `Comment`. `Page` and `Person` are linked many-to-many through a `page_employees` join table, representing the people who work at that page.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/pages/{page_id}` | Get full details of a page (DB-first, scrapes if not found) |
| GET | `/pages` | List/search pages, with filters |
| GET | `/pages/{page_id}/posts` | Paginated posts for a page |
| GET | `/pages/{page_id}/people` | Paginated employees for a page |

### Filters on `GET /pages`

- `name` – partial, case-insensitive match on page name
- `industry` – partial match on industry
- `min_followers` / `max_followers` – follower count range
- `skip` / `limit` – pagination

Example:
```
GET /pages?industry=Software Development&min_followers=1000&limit=5
```

A ready-to-use Postman collection is included as `postman_collection.json` — import it directly into Postman to try all endpoints.

## Design notes

- **Service layer** – scraping and database logic are kept separate from the API routes (`services/page_service.py`), so routes stay thin and the scraping logic can be reused or tested independently.
- **DB-first, scrape-on-demand** – `GET /pages/{page_id}` checks the database first. Only if the page doesn't exist does it trigger a live scrape, save the result, and return it. This is handled by `get_or_create_page()`.
- **Sub-resource endpoints don't scrape** – `/posts` and `/people` expect the page to already exist in the DB (via the main endpoint first) and return a 404 if it doesn't, rather than triggering their own scrape. This keeps the scrape-triggering logic in one place.
- **No refresh/upsert logic** – once a page is scraped and saved, re-requesting it serves the existing DB record rather than re-scraping. This was a deliberate scope decision given the timeline; a `force_refresh` option would be a natural next addition.

## Known limitations (scraping-related)

LinkedIn is not a stable, documented API — scraping it comes with a few real constraints worth being upfront about:

- **LinkedIn serves at least two different page layouts** for company pages (an older template with clean, semantic class names, and a newer one with obfuscated, auto-generated classes — seemingly tied to page size/verification). This scraper handles both, using the stable selectors first and falling back to text-anchored searches (e.g. finding a field by its label text) when they don't match.
- **`specialities`** isn't present on every page (smaller/newer companies often haven't filled it in) and is only scraped on a best-effort basis.
- **Follower identities aren't scraped**, only the follower *count*. LinkedIn doesn't expose an actual list of followers for a page, even to a logged-in scraper — so "people associated with a page" in this project means employees, not followers.
- **`posted_at`** is stored as LinkedIn's relative time string (e.g. `"6mo"`, `"2d"`) rather than an exact date, since LinkedIn doesn't expose an absolute timestamp anywhere in the page's HTML.
- **`headcount`** is stored as the range string LinkedIn shows (e.g. `"2-10 employees"`), not a single number, since that's the only granularity LinkedIn provides.
- **`Person.headline`** is stored exactly as scraped, which sometimes includes someone's past roles alongside their current one, since it's free text and not reliably separable.
- Comments are loaded with a bounded number of "load more" clicks (not unlimited), and posts are capped at a configurable maximum (default ~20), to keep scrape time and load on LinkedIn reasonable.

## A note on scraping LinkedIn

Scraping LinkedIn isn't something LinkedIn's Terms of Service allow, even though scraping publicly visible data isn't clearly illegal in most places (see *hiQ Labs v. LinkedIn*). In practice this mainly means a real risk of the scraping account getting rate-limited or banned. For that reason:

- This project uses a secondary LinkedIn account for scraping, not a primary one.
- The scraper reuses a single saved login session rather than logging in repeatedly.
- It's built and tested for scraping a small number of pages for demo purposes, not high-volume or continuous scraping.

## Environment file reference

```
DB_URL=mysql+pymysql://<user>:<password>@localhost:3306/linkedin_insights
```