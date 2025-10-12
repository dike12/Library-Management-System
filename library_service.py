"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_patron_borrowed_books, get_db_connection
)

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed > 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    Implements R4: Book Return Processing
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to return
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    

    # Check if book exists
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    # Get patron's borrowed books
    borrowed_books = get_patron_borrowed_books(patron_id)
    print(borrowed_books)
    
    # Check if the book is borrowed by this patron
    book_borrowed = False
    due_date = None
    for borrowed in borrowed_books:
        if borrowed['book_id'] == book_id:
            book_borrowed = True
            due_date = borrowed['due_date']
            break
    
    if not book_borrowed:
        return False, "This book was not borrowed by this patron."

    # Process return
    return_date = datetime.now()
    
    # Update borrow record
    update_success = update_borrow_record_return_date(
        patron_id, 
        book_id, 
        return_date
    )
    if not update_success:
        return False, "Database error occurred while updating return record."
    
    # Update book availability
    availability_success = update_book_availability(book_id, 1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    # Calculate late fee if applicable
    if return_date.date() > due_date.date():
        days_late = (return_date.date() - due_date.date()).days
        fee_amount = days_late * 0.50  # $0.50 per day late
        return True, f'Book returned successfully but {days_late} days late. Late fee: ${fee_amount:.2f}'
    
    return True, f'Book "{book["title"]}" has been successfully returned.'

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
    Implements R5: Late Fee Calculation
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to check
        
    Returns:
        dict: Contains fee amount, days overdue, and status
    """
    # Input validation
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Invalid patron ID'
        }
    
    # Check if book exists
    book = get_book_by_id(book_id)
    if not book:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book not found'
        }
    
    # Get patron's borrowed books
    borrowed_books = get_patron_borrowed_books(patron_id)
    
    # Find this book in patron's borrowed books
    book_record = None
    for borrowed in borrowed_books:
        if borrowed['book_id'] == book_id:
            book_record = borrowed
            break
    
    if not book_record:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book not borrowed by this patron'
        }
    
    # Calculate days overdue
    current_date = datetime.now().date()
    due_date = book_record['due_date'].date()
    
    if current_date <= due_date:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book not overdue'
        }
    
    days_overdue = (current_date - due_date).days

    # Calculate fee based on days overdue
    fee_amount = 0.00
    if days_overdue <= 7:
        fee_amount = days_overdue * 0.50  # $0.50 per day for first 7 days
    else:
        fee_amount = (7 * 0.50) + ((days_overdue - 7) * 1.00)  # $1.00 per day after 7 days
    
    # Cap fee at maximum $15.00
    fee_amount = min(fee_amount, 15.00)
    
    return {
        'fee_amount': round(fee_amount, 2),
        'days_overdue': days_overdue,
        'status': 'Late fee calculated'
    }

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    Implements R6: Book Search Functionality

    Args:
        search_term: Term to search for
        search_type: Type of search (title, author, or isbn)

    Returns:
        List[Dict]: List of matching books
    """
    # Input validation
    if not search_term or not search_term.strip():
        return []

    # Validate search type
    valid_search_types = ['title', 'author', 'isbn']
    if search_type not in valid_search_types:
        return []

    # Clean search term
    search_term = search_term.strip()

    # Get database connection
    conn = get_db_connection()

    try:
        if search_type == 'isbn':
            # Exact match for ISBN
            books = conn.execute('''
                SELECT * FROM books 
                WHERE isbn = ?
                ORDER BY title
            ''', (search_term,)).fetchall()
        else:
            # Partial match for title or author
            search_pattern = f'%{search_term}%'
            books = conn.execute(f'''
                SELECT * FROM books 
                WHERE {search_type} LIKE ? COLLATE NOCASE
                ORDER BY title
            ''', (search_pattern,)).fetchall()

        # Convert to list of dictionaries
        results = []
        for book in books:
            results.append({
                'id': book['id'],
                'title': book['title'],
                'author': book['author'],
                'isbn': book['isbn'],
                'total_copies': book['total_copies'],
                'available_copies': book['available_copies']
            })

        return results

    except Exception as e:
        print(f"Search error: {str(e)}")
        return []

    finally:
        conn.close()

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.
    Implements R7: Patron Status Report
    
    Args:
        patron_id: 6-digit library card ID
        
    Returns:
        dict: Contains patron's borrowing status and history
    """
    # Input validation
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            'error': 'Invalid patron ID. Must be exactly 6 digits.',
            'current_books': [],
            'total_borrowed': 0,
            'total_fees': 0.00,
            'borrow_history': []
        }
    
    # Get database connection
    conn = get_db_connection()
    
    try:
        # Get currently borrowed books
        current_books = get_patron_borrowed_books(patron_id)
        
        # Calculate total late fees
        total_fees = 0.00
        for book in current_books:
            if book['is_overdue']:
                fee_info = calculate_late_fee_for_book(patron_id, book['book_id'])
                total_fees += fee_info['fee_amount']
        
        # Get complete borrowing history
        history = conn.execute('''
            SELECT 
                br.*, 
                b.title, 
                b.author,
                b.isbn
            FROM borrow_records br
            JOIN books b ON br.book_id = b.id
            WHERE br.patron_id = ?
            ORDER BY br.borrow_date DESC
        ''', (patron_id,)).fetchall()

        # Format borrowing history
        borrow_history = []
        for record in history:
            borrow_history.append({
                'book_id': record['book_id'],
                'title': record['title'],
                'author': record['author'],
                'isbn': record['isbn'],
                'borrow_date': datetime.fromisoformat(record['borrow_date']).strftime('%Y-%m-%d'),
                'due_date': datetime.fromisoformat(record['due_date']).strftime('%Y-%m-%d'),
                'return_date': datetime.fromisoformat(record['return_date']).strftime('%Y-%m-%d') if record['return_date'] else None,
                'status': 'Returned' if record['return_date'] else 'Borrowed'
            })
        
        return {
            'current_books': [{
                'book_id': book['book_id'],
                'title': book['title'],
                'author': book['author'],
                'due_date': book['due_date'].strftime('%Y-%m-%d'),
                'is_overdue': book['is_overdue']
            } for book in current_books],
            'total_borrowed': len(current_books),
            'total_fees': round(total_fees, 2),
            'borrow_history': borrow_history
        }
        
    except Exception as e:
        print(f"Error generating patron status report: {str(e)}")
        return {
            'error': 'Database error occurred while generating report.',
            'current_books': [],
            'total_borrowed': 0,
            'total_fees': 0.00,
            'borrow_history': []
        }
    
    finally:
        conn.close()
