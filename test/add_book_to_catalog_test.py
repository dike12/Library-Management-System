import pytest
import sys
sys.path.insert(0, '../')

from database import init_database
init_database()


from library_service import add_book_to_catalog



class TestAddBookToCatalog:
    """Test suite for R1: Add Book To Catalog functionality"""
    
    def test_add_book_valid_input(self):
        """
        Positive test: Add book with all valid inputs
        Expected: Success with confirmation message
        """
        success, message = add_book_to_catalog("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 3)
        
        assert success == True
        assert "successfully added" in message.lower()
        assert "The Great Gatsby" in message
    
    def test_add_book_minimal_valid_input(self):
        """
        Positive test: Add book with minimal valid data (single character title/author)
        Expected: Success
        """
        success, message = add_book_to_catalog("A", "B", "1234567890123", 1)
        
        assert success == True
        assert "successfully added" in message.lower()
    
    def test_add_book_maximum_length_inputs(self):
        """
        Positive test: Add book with maximum allowed character lengths
        Expected: Success
        """
        long_title = "A" * 200  # Exactly 200 characters
        long_author = "B" * 100  # Exactly 100 characters
        
        success, message = add_book_to_catalog(long_title, long_author, "9876543210987", 5)
        
        assert success == True
        assert "successfully added" in message.lower()
    
    def test_add_book_whitespace_trimming(self):
        """
        Positive test: Verify whitespace is properly trimmed from title and author
        Expected: Success with trimmed values
        """
        success, message = add_book_to_catalog("  Spaced Title  ", "  Spaced Author  ", "1111111111111", 2)
        
        assert success == True
        assert "Spaced Title" in message  # Should not include extra spaces
    
    def test_add_book_empty_title(self):
        """
        Negative test: Empty title
        Expected: Failure with appropriate error message
        """
        success, message = add_book_to_catalog("", "Valid Author", "1234567890123", 1)
        
        assert success == False
        assert "title is required" in message.lower()
    
    def test_add_book_whitespace_only_title(self):
        """
        Negative test: Title with only whitespace
        Expected: Failure with appropriate error message
        """
        success, message = add_book_to_catalog("   ", "Valid Author", "1234567890123", 1)
        
        assert success == False
        assert "title is required" in message.lower()
    
    def test_add_book_title_too_long(self):
        """
        Negative test: Title exceeds 200 character limit
        Expected: Failure with length validation error
        """
        long_title = "A" * 201  # 201 characters (over limit)
        success, message = add_book_to_catalog(long_title, "Valid Author", "1234567890123", 1)
        
        assert success == False
        assert "200 characters" in message
    
    def test_add_book_empty_author(self):
        """
        Negative test: Empty author
        Expected: Failure with appropriate error message
        """
        success, message = add_book_to_catalog("Valid Title", "", "1234567890123", 1)
        
        assert success == False
        assert "author is required" in message.lower()
    
    def test_add_book_author_too_long(self):
        """
        Negative test: Author exceeds 100 character limit
        Expected: Failure with length validation error
        """
        long_author = "B" * 101  # 101 characters (over limit)
        success, message = add_book_to_catalog("Valid Title", long_author, "1234567890123", 1)
        
        assert success == False
        assert "100 characters" in message
    
    def test_add_book_isbn_too_short(self):
        """
        Negative test: ISBN with less than 13 digits
        Expected: Failure with ISBN validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "123456789", 1)
        
        assert success == False
        assert "13 digits" in message
    
    def test_add_book_isbn_too_long(self):
        """
        Negative test: ISBN with more than 13 digits
        Expected: Failure with ISBN validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "12345678901234", 1)
        
        assert success == False
        assert "13 digits" in message
    
    def test_add_book_isbn_with_letters(self):
        """
        Negative test: ISBN containing non-digit characters
        Expected: Failure with ISBN validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "123456789012A", 1)
        
        assert success == False
        assert "13 digits" in message
    
    def test_add_book_zero_copies(self):
        """
        Negative test: Zero total copies
        Expected: Failure with positive integer validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "1234567890123", 0)
        
        assert success == False
        assert "positive integer" in message
    
    def test_add_book_negative_copies(self):
        """
        Negative test: Negative total copies
        Expected: Failure with positive integer validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "1234567890123", -1)
        
        assert success == False
        assert "positive integer" in message
    
    def test_add_book_non_integer_copies(self):
        """
        Negative test: Non-integer total copies (string)
        Expected: Failure with integer validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "1234567890123", "5")
        
        assert success == False
        assert "positive integer" in message
    
    def test_add_book_float_copies(self):
        """
        Negative test: Float value for total copies
        Expected: Failure with integer validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "1234567890123", 5.5)
        
        assert success == False
        assert "positive integer" in message

    #Added from A2

    def test_add_book_special_characters_in_title(self):
        """
        Positive test: Title containing special characters
        Expected: Success
        """
        success, message = add_book_to_catalog("Book! @#$%^&*()", "Valid Author", "1234567890123", 1)
        
        assert success == True
        assert "successfully added" in message.lower()

    def test_add_book_unicode_characters(self):
        """
        Positive test: Title and author with Unicode characters
        Expected: Success
        """
        success, message = add_book_to_catalog("título del libro", "José García", "1234567890123", 1)
        
        assert success == True
        assert "successfully added" in message.lower()

    def test_add_book_numbers_in_title(self):
        """
        Positive test: Title containing numbers
        Expected: Success
        """
        success, message = add_book_to_catalog("Book 123", "Valid Author", "1234567890123", 1)
        
        assert success == True
        assert "successfully added" in message.lower()

    def test_add_book_duplicate_title_different_isbn(self):
        """
        Positive test: Same title but different ISBN
        Expected: Success
        """
        add_book_to_catalog("Duplicate Title", "Author One", "1111111111111", 1)
        success, message = add_book_to_catalog("Duplicate Title", "Author Two", "2222222222222", 1)
        
        assert success == True
        assert "successfully added" in message.lower()

    def test_add_book_max_copies(self):
        """
        Positive test: Large number of copies
        Expected: Success
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "1234567890123", 999999)
        
        assert success == True
        assert "successfully added" in message.lower()

    def test_add_book_title_only_numbers(self):
        """
        Positive test: Title consisting only of numbers
        Expected: Success
        """
        success, message = add_book_to_catalog("12345", "Valid Author", "1234567890123", 1)
        
        assert success == True
        assert "successfully added" in message.lower()

    def test_add_book_null_title(self):
        """
        Negative test: None as title
        Expected: Failure with appropriate error message
        """
        success, message = add_book_to_catalog(None, "Valid Author", "1234567890123", 1)
        
        assert success == False
        assert "title is required" in message.lower()

    def test_add_book_null_author(self):
        """
        Negative test: None as author
        Expected: Failure with appropriate error message
        """
        success, message = add_book_to_catalog("Valid Title", None, "1234567890123", 1)
        
        assert success == False
        assert "author is required" in message.lower()

    def test_add_book_invalid_isbn_letters_and_numbers(self):
        """
        Negative test: ISBN with mix of letters and numbers but correct length
        Expected: Failure with ISBN validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "12345ABC67890", 1)
        
        assert success == False
        assert "13 digits" in message

    def test_add_book_special_characters_in_isbn(self):
        """
        Negative test: ISBN with special characters
        Expected: Failure with ISBN validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "123456!@#$%90", 1)
        
        assert success == False
        assert "13 digits" in message

