import pytest
import sys
sys.path.insert(0, '../')

from database import init_database
init_database()


from library_service import borrow_book_by_patron
from datetime import datetime, timedelta


class TestBorrowBookByPatron:
    """Test suite for R3: Book Borrowing functionality"""
    
    def test_borrow_book_valid_request(self):
        """
        Positive test: Valid patron borrows available book
        Expected: Success with due date message
        """
        # Use a book that should be available (book_id=1 from sample data)
        success, message = borrow_book_by_patron("123456", 1)
        
        assert success == True
        assert "successfully borrowed" in message.lower()
        assert "due date:" in message.lower()
        # Check due date format (should be 14 days from now)
        assert datetime.now().strftime("%Y-%m") in message
    
    def test_borrow_book_different_valid_patron(self):
        """
        Positive test: Different valid patron borrows book
        Expected: Success
        """
        success, message = borrow_book_by_patron("654321", 2)
        
        assert success == True
        assert "successfully borrowed" in message.lower()
    
    # Patron ID Validation Tests
    def test_borrow_book_empty_patron_id(self):
        """
        Negative test: Empty patron ID
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron("", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower()
        assert "6 digits" in message
    
    def test_borrow_book_none_patron_id(self):
        """
        Negative test: None patron ID
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron(None, 1)
        
        assert success == False
        assert "invalid patron id" in message.lower()
    
    def test_borrow_book_patron_id_too_short(self):
        """
        Negative test: Patron ID less than 6 digits
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron("12345", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower()
        assert "6 digits" in message
    
    def test_borrow_book_patron_id_too_long(self):
        """
        Negative test: Patron ID more than 6 digits
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron("1234567", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower()
        assert "6 digits" in message
    
    def test_borrow_book_patron_id_with_letters(self):
        """
        Negative test: Patron ID containing non-digit characters
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron("12345A", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower()
        assert "6 digits" in message
    
    def test_borrow_book_patron_id_with_spaces(self):
        """
        Negative test: Patron ID with spaces
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron("12 34 56", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower()
    
    # Book Validation Tests
    def test_borrow_nonexistent_book(self):
        """
        Negative test: Try to borrow book that doesn't exist
        Expected: Failure with book not found error
        """
        success, message = borrow_book_by_patron("123456", 99999)
        
        assert success == False
        assert "book not found" in message.lower()
    
    def test_borrow_unavailable_book(self):
        """
        Negative test: Try to borrow book with 0 available copies
        Expected: Failure with availability error
        """
        # Book ID 3 should be unavailable from sample data
        success, message = borrow_book_by_patron("123456", 3)
        
        assert success == False
        assert "not available" in message.lower()
    
    def test_borrow_book_negative_book_id(self):
        """
        Negative test: Negative book ID
        Expected: Failure with book not found
        """
        success, message = borrow_book_by_patron("123456", -1)
        
        assert success == False
        assert "book not found" in message.lower()
    
    def test_borrow_book_zero_book_id(self):
        """
        Negative test: Zero book ID
        Expected: Failure with book not found
        """
        success, message = borrow_book_by_patron("123456", 0)
        
        assert success == False
        assert "book not found" in message.lower()

    # added from A2

    def test_borrow_multiple_books_within_limit(self):
        """
        Positive test: Patron borrows multiple books within 5-book limit
        Expected: Success for each borrow
        """
        patron_id = "111111"
        
        # Borrow 3 different books
        success1, _ = borrow_book_by_patron(patron_id, 1)
        success2, _ = borrow_book_by_patron(patron_id, 2)
        success3, _ = borrow_book_by_patron(patron_id, 4)
        
        assert success1 == True
        assert success2 == True
        assert success3 == True
    
    def test_borrow_exceeding_limit(self):
        """
        Negative test: Patron attempts to borrow more than 5 books
        Expected: Failure with limit exceeded message
        """
        patron_id = "222222"
        
        # Borrow 5 books first
        for book_id in range(1, 6):
            borrow_book_by_patron(patron_id, book_id)
        
        # Try to borrow 6th book
        success, message = borrow_book_by_patron(patron_id, 6)
        
        assert success == False
        assert "maximum borrowing limit" in message.lower()
        assert "5 books" in message
    
    def test_borrow_same_book_twice(self):
        """
        Negative test: Patron attempts to borrow same book twice
        Expected: Failure with availability error
        """
        patron_id = "333333"
        
        # Borrow book first time
        success1, _ = borrow_book_by_patron(patron_id, 1)
        # Try to borrow same book again
        success2, message = borrow_book_by_patron(patron_id, 1)
        
        assert success1 == True
        assert success2 == False
        assert "not available" in message.lower()
    
    def test_borrow_book_due_date_calculation(self):
        """
        Positive test: Verify due date is exactly 14 days from borrow date
        Expected: Success with correct due date
        """
        success, message = borrow_book_by_patron("444444", 1)
        
        assert success == True
        expected_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        assert expected_date in message
    
    def test_borrow_book_last_copy(self):
        """
        Positive test: Borrow last available copy of a book
        Expected: Success and book becomes unavailable
        """
        patron_id = "555555"
        book_id = 2  # Assuming this book has limited copies
        
        # Borrow last copy
        success1, _ = borrow_book_by_patron(patron_id, book_id)
        # Try to borrow again
        success2, message = borrow_book_by_patron("666666", book_id)
        
        assert success1 == True
        assert success2 == False
        assert "not available" in message.lower()
    
    def test_borrow_book_concurrent_requests(self):
        """
        Test concurrent borrowing requests for same book
        Expected: Only one request should succeed
        """
        patron1_id = "777777"
        patron2_id = "888888"
        book_id = 1
        
        # Simulate concurrent requests
        success1, _ = borrow_book_by_patron(patron1_id, book_id)
        success2, message2 = borrow_book_by_patron(patron2_id, book_id)
        
        assert success1 == True
        assert (success1 and not success2) or (not success1 and success2)
    
    def test_borrow_book_float_book_id(self):
        """
        Negative test: Book ID as float
        Expected: Failure with invalid book ID
        """
        success, message = borrow_book_by_patron("123456", 1.5)
        
        assert success == False
        assert "book not found" in message.lower()
    
    def test_borrow_book_special_chars_patron_id(self):
        """
        Negative test: Patron ID with special characters
        Expected: Failure with invalid patron ID
        """
        success, message = borrow_book_by_patron("12@456", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower()
    
    def test_borrow_book_whitespace_patron_id(self):
        """
        Negative test: Patron ID with leading/trailing whitespace
        Expected: Failure with invalid patron ID
        """
        success, message = borrow_book_by_patron(" 123456 ", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower()