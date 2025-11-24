import uuid
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5000"


def make_isbn() -> str:
    """Return a random 13-digit ISBN string."""
    # 978 prefix + 10 random digits
    return "978" + str(uuid.uuid4().int)[:10]


def add_book_via_ui(page: Page, title: str, author: str, isbn: str, copies: int):
    """Helper that uses the real Add Book form."""
    # Go to home, then click "Add Book" in the nav bar
    page.goto(f"{BASE_URL}/")
    page.locator("a:has-text('Add Book')").click()

    # Fill form (IDs from add_book.html)
    page.fill("input#title", title)
    page.fill("input#author", author)
    page.fill("input#isbn", isbn)
    page.fill("input#total_copies", str(copies))

    # Click the submit button (text from add_book.html)
    page.get_by_role("button", name="Add Book to Catalog").click()

    # After success, route redirects to catalog page
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("📖 Book Catalog")).to_be_visible()


def test_add_book_appears_in_catalog(page: Page):
    """
    Flow 1:
      - Navigate to Add Book via navbar
      - Fill form with valid data
      - Submit
      - Verify the new book appears in the catalog table
    """
    title = f"E2E Test Book {uuid.uuid4()}"
    author = "E2E Author"
    isbn = make_isbn()
    copies = 3

    add_book_via_ui(page, title, author, isbn, copies)

    # Assert: the new book is shown in the catalog table
    row = page.locator("tbody tr", has_text=title).first
    expect(row).to_be_visible()
    expect(row.get_by_text(author)).to_be_visible()
    expect(row.get_by_text(isbn)).to_be_visible()
    # Availability cell should contain "Available"
    expect(row.get_by_text("Available")).to_be_visible()


def test_borrow_book_and_patron_status(page: Page):
    """
    Flow 2:
      - Add a book
      - Borrow it from the catalog using a 6-digit patron ID
      - Verify borrow success flash message
      - Navigate to Patron Status, search by same patron ID
      - Verify the borrowed book shows up in patron status tables
    """
    title = f"E2E Borrow Book {uuid.uuid4()}"
    author = "Borrow Author"
    isbn = make_isbn()
    copies = 2
    patron_id = "123456"  # must be 6 digits, matches your validation

    # 1) Add the book
    add_book_via_ui(page, title, author, isbn, copies)

    # 2) Borrow from the catalog
    row = page.locator("tbody tr", has_text=title).first
    expect(row).to_be_visible()

    # Fill inline patron ID field in that row (from catalog.html)
    row.locator("input[name='patron_id']").fill(patron_id)

    # Click the "Borrow" button in that row
    row.get_by_role("button", name="Borrow").click()

    # Wait for any redirect / reload
    page.wait_for_load_state("networkidle")

    # 3) Assert a success flash message appears
    success_flash = page.locator(".flash-success").first
    expect(success_flash).to_be_visible()
    expect(success_flash).to_contain_text("Successfully borrowed")

    # 4) Navigate to Patron Status via navbar
    page.locator("a:has-text('Patron Status')").click()

    # Fill Patron ID form on patron.html
    page.fill("input#patron_id", patron_id)
    page.get_by_role("button", name="View Status").click()

    page.wait_for_load_state("networkidle")

    # 5) Assert the borrowed book shows up somewhere in the status tables
    borrowed_row = page.locator("tr", has_text=title).first
    expect(borrowed_row).to_be_visible()


def test_return_book_flow(page: Page):
    """
    Flow 3:
      - Add a book
      - Borrow it from the catalog
      - Go to Return Book page
      - Return using Patron ID + Book ID
      - Verify success flash message
    """
    title = f"E2E Return Book {uuid.uuid4()}"
    author = "Return Author"
    isbn = make_isbn()
    copies = 1
    patron_id = "234567"

    # 1) Add the book
    add_book_via_ui(page, title, author, isbn, copies)

    # 2) Borrow the book so it can be returned
    row = page.locator("tbody tr", has_text=title).first
    expect(row).to_be_visible()

    # Get book ID from first <td> in the row (catalog.html: first column is ID)
    book_id_text = row.locator("td").nth(0).text_content().strip()
    book_id = int(book_id_text)

    # Fill inline patron ID and borrow
    row.locator("input[name='patron_id']").fill(patron_id)
    row.get_by_role("button", name="Borrow").click()
    page.wait_for_load_state("networkidle")

    # Confirm borrow succeeded
    success_flash = page.locator(".flash-success").first
    expect(success_flash).to_be_visible()
    expect(success_flash).to_contain_text("Successfully borrowed")

    # 3) Navigate to Return Book via navbar
    page.locator("a:has-text('Return Book')").click()

    # 4) Fill return form (IDs from return_book.html)
    page.fill("input#patron_id", patron_id)
    page.fill("input#book_id", str(book_id))

    page.get_by_role("button", name="Process Return").click()
    page.wait_for_load_state("networkidle")

    # 5) Assert success flash message about returning
    return_flash = page.locator(".flash-success").first
    expect(return_flash).to_be_visible()
    # Message text could be "Book returned successfully..." or similar
    expect(return_flash).to_contain_text("returned")


def test_search_finds_added_book(page: Page):
    """
    Flow 4:
      - Add a book
      - Go to Search page
      - Search by partial title using Title search
      - Verify it appears in the search results table
    """
    full_title = f"E2E Search Book {uuid.uuid4()}"
    author = "Search Author"
    isbn = make_isbn()
    copies = 4

    # 1) Add the book
    add_book_via_ui(page, full_title, author, isbn, copies)

    # 2) Navigate to Search via navbar
    page.locator("a:has-text('Search')").click()

    # Use a partial title to test partial matching
    partial_title = full_title[:15]

    # Fill search form (search.html)
    page.fill("input#q", partial_title)
    # "title" is already default, but set it explicitly for clarity
    page.select_option("select#type", "title")

    # Click the Search button
    # The visual text is "🔍 Search", but accessible name should at least contain "Search"
    page.get_by_role("button", name="Search").click()

    page.wait_for_load_state("networkidle")

    # 3) Assert results table contains our book
    row = page.locator("tbody tr", has_text=full_title).first
    expect(row).to_be_visible()
    expect(row.get_by_text(author)).to_be_visible()
    expect(row.get_by_text(isbn)).to_be_visible()
