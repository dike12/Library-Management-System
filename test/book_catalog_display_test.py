import pytest
import sys
sys.path.insert(0, '../')

from database import init_database, add_sample_data
from library_service import get_all_books, add_book_to_catalog

class TestBookCatalogDisplay:

    def setup_database(self):
        """Initialize database before each test"""
        init_database()
        add_sample_data()
    
    def test_get_all_books_not_empty(self):
        """
        Test that catalog returns books when database is populated
        Expected: List containing at least one book
        """
        books = get_all_books()
        assert len(books) > 0
        assert isinstance(books, list)
    
    def test_book_catalog_structure(self):
        """
        Test that each book entry contains all required fields
        Expected: All required fields present with correct types
        """
        books = get_all_books()
        required_fields = ['id', 'title', 'author', 'isbn', 'total_copies', 'available_copies']
        
        for book in books:
            assert isinstance(book, dict)
            for field in required_fields:
                assert field in book
            
            # Verify field types
            assert isinstance(book['id'], int)
            assert isinstance(book['title'], str)
            assert isinstance(book['author'], str)
            assert isinstance(book['isbn'], str)
            assert isinstance(book['total_copies'], int)
            assert isinstance(book['available_copies'], int)
    
    def test_available_copies_less_or_equal_total(self):
        """
        Test that available copies is always <= total copies
        Expected: Available copies not exceeding total copies
        """
        books = get_all_books()
        for book in books:
            assert book['available_copies'] <= book['total_copies']
            assert book['available_copies'] >= 0
    
    def test_catalog_alphabetical_order(self):
        """
        Test that books are returned in alphabetical order by title
        Expected: Books sorted alphabetically by title
        """
        books = get_all_books()
        titles = [book['title'] for book in books]
        sorted_titles = sorted(titles)
        assert titles == sorted_titles
    
    def test_newly_added_book_appears(self):
        """
        Test that newly added books appear in catalog
        Expected: New book present in catalog
        """
        new_book = {
            'title': 'New Test Book',
            'author': 'Test Author',
            'isbn': '1234567890123',
            'total_copies': 1
        }
        
        add_book_to_catalog(new_book['title'], new_book['author'], new_book['isbn'], new_book['total_copies'])
        
        books = get_all_books()
        found = False
        for book in books:
            if (book['title'] == new_book['title'] and 
                book['author'] == new_book['author'] and 
                book['isbn'] == new_book['isbn']):
                found = True
                break
        
        assert found == True
    
    def test_catalog_with_zero_available_copies(self):
        """
        Test display of books with zero available copies
        Expected: Books with zero copies still displayed
        """
        books = get_all_books()
        unavailable_books = [book for book in books if book['available_copies'] == 0]
        assert len(unavailable_books) > 0
    
    def test_unique_book_ids(self):
        """
        Test that all book IDs in catalog are unique
        Expected: No duplicate IDs
        """
        books = get_all_books()
        book_ids = [book['id'] for book in books]
        assert len(book_ids) == len(set(book_ids))
    
    def test_valid_isbn_format(self):
        """
        Test that all ISBNs in catalog are valid 13-digit numbers
        Expected: All ISBNs are 13 digits
        """
        books = get_all_books()
        for book in books:
            assert len(book['isbn']) == 13
            assert book['isbn'].isdigit()
    
    def test_non_empty_required_fields(self):
        """
        Test that no required fields are empty
        Expected: No empty required fields
        """
        books = get_all_books()
        for book in books:
            assert book['title'].strip() != ""
            assert book['author'].strip() != ""
            assert book['isbn'].strip() != ""
    
    def test_positive_copy_numbers(self):
        """
        Test that copy numbers are non-negative
        Expected: All copy counts >= 0
        """
        books = get_all_books()
        for book in books:
            assert book['total_copies'] > 0
            assert book['available_copies'] >= 0

    def test_empty_catalog_after_init(self):
        """
        Test catalog state with fresh database
        Expected: Empty list when no books added
        """
        init_database()  # Reset database without sample data
        books = get_all_books()
        assert len(books) == 0
        assert isinstance(books, list)
    
    def test_multiple_copies_display(self):
        """
        Test display of books with multiple copies
        Expected: Correct total and available copy counts
        """
        add_book_to_catalog("Multiple Copies Book", "Test Author", "9999999999999", 5)
        
        books = get_all_books()
        multi_copy_book = None
        for book in books:
            if book['isbn'] == "9999999999999":
                multi_copy_book = book
                break
        
        assert multi_copy_book is not None
        assert multi_copy_book['total_copies'] == 5
        assert multi_copy_book['available_copies'] == 5