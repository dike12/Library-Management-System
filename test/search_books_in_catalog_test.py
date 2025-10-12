import pytest
import sys
sys.path.insert(0, '../')

from database import init_database
init_database()


from library_service import search_books_in_catalog

class TestSearchBooksValidation:
    """Test search parameter validation"""
    
    def test_search_empty_search_term(self):
        """
        Test: Empty search term
        Expected: Should return empty list or all books
        """
        result = search_books_in_catalog("", "title")
        
        assert isinstance(result, list)
        # Could return empty list or all books - both are valid approaches
    
    def test_search_none_search_term(self):
        """
        Test: None search term
        Expected: Should handle gracefully
        """
        result = search_books_in_catalog(None, "title")
        
        assert isinstance(result, list)
        # Should not crash, return empty list
    
    def test_search_whitespace_only_search_term(self):
        """
        Test: Search term with only whitespace
        Expected: Should handle gracefully, likely return empty results
        """
        result = search_books_in_catalog("   ", "title")
        
        assert isinstance(result, list)
    
    def test_search_invalid_search_type(self):
        """
        Test: Invalid search type
        Expected: Should default to title search or return empty
        """
        result = search_books_in_catalog("test", "invalid_type")
        
        assert isinstance(result, list)
    
    def test_search_none_search_type(self):
        """
        Test: None search type
        Expected: Should default to title search
        """
        result = search_books_in_catalog("test", None)
        
        assert isinstance(result, list)
    
    def test_search_case_insensitive_search_type(self):
        """
        Test: Search type with different cases
        Expected: Should accept TITLE, Title, title, etc.
        """
        result = search_books_in_catalog("gatsby", "TITLE")
        
        assert isinstance(result, list)

class TestSearchBooksByTitle:
    """Test title search functionality"""
    
    def test_search_exact_title_match(self):
        """
        Test: Exact title match for "The Great Gatsby"
        Expected: Should return exactly one matching book
        """
        result = search_books_in_catalog("The Great Gatsby", "title")
        
        assert len(result) == 1
        assert result[0]['title'] == "The Great Gatsby"
        assert result[0]['author'] == "F. Scott Fitzgerald"
    
    def test_search_partial_title_match(self):
        """
        Test: Partial title match (case-insensitive) for "gatsby"
        Expected: Should return "The Great Gatsby"
        """
        result = search_books_in_catalog("gatsby", "title")
        
        assert len(result) == 1
        assert "gatsby" in result[0]['title'].lower()
        assert result[0]['title'] == "The Great Gatsby"
    
    def test_search_title_case_insensitive(self):
        """
        Test: Case insensitive title search for "GREAT GATSBY"
        Expected: Should find "The Great Gatsby"
        """
        result = search_books_in_catalog("GREAT GATSBY", "title")
        
        assert len(result) == 1
        assert result[0]['title'] == "The Great Gatsby"
    
    def test_search_numeric_title(self):
        """
        Test: Search for numeric title "1984"
        Expected: Should return the book "1984" by George Orwell
        """
        result = search_books_in_catalog("1984", "title")
        
        assert len(result) == 1
        assert result[0]['title'] == "1984"
        assert result[0]['author'] == "George Orwell"
    
    def test_search_title_with_partial_word(self):
        """
        Test: Search for "Kill" should find "To Kill a Mockingbird"
        Expected: Should return matching book
        """
        result = search_books_in_catalog("Kill", "title")
        
        assert len(result) == 1
        assert result[0]['title'] == "To Kill a Mockingbird"
        assert result[0]['author'] == "Harper Lee"
    
    def test_search_nonexistent_title(self):
        """
        Test: Search for title that doesn't exist
        Expected: Should return empty list
        """
        result = search_books_in_catalog("Nonexistent Book Title XYZ", "title")
        
        assert len(result) == 0

class TestSearchBooksByAuthor:
    """Test author search functionality"""
    
    def test_search_exact_author_name(self):
        """
        Test: Exact author name "George Orwell"
        Expected: Should return "1984"
        """
        result = search_books_in_catalog("George Orwell", "author")
        
        assert len(result) == 1
        assert result[0]['author'] == "George Orwell"
        assert result[0]['title'] == "1984"
    
    def test_search_partial_author_last_name(self):
        """
        Test: Partial author search "Orwell"
        Expected: Should return book by George Orwell
        """
        result = search_books_in_catalog("Orwell", "author")
        
        assert len(result) == 1
        assert "orwell" in result[0]['author'].lower()
        assert result[0]['title'] == "1984"
    
    def test_search_partial_author_first_name(self):
        """
        Test: Search by first name "Harper"
        Expected: Should return book by Harper Lee
        """
        result = search_books_in_catalog("Harper", "author")
        
        assert len(result) == 1
        assert "Harper" in result[0]['author']
        assert result[0]['title'] == "To Kill a Mockingbird"
    
    def test_search_author_case_insensitive(self):
        """
        Test: Case insensitive author search "f. scott fitzgerald"
        Expected: Should find "The Great Gatsby"
        """
        result = search_books_in_catalog("f. scott fitzgerald", "author")
        
        assert len(result) == 1
        assert result[0]['author'] == "F. Scott Fitzgerald"
        assert result[0]['title'] == "The Great Gatsby"
    
    def test_search_nonexistent_author(self):
        """
        Test: Search for author that doesn't exist
        Expected: Should return empty list
        """
        result = search_books_in_catalog("Nonexistent Author XYZ", "author")
        
        assert len(result) == 0

class TestSearchBooksByISBN:
    """Test ISBN search functionality"""
    
    def test_search_exact_isbn_gatsby(self):
        """
        Test: Exact ISBN search for "The Great Gatsby"
        Expected: Should return exactly one book
        """
        result = search_books_in_catalog("9780743273565", "isbn")
        
        assert len(result) == 1
        assert result[0]['isbn'] == "9780743273565"
        assert result[0]['title'] == "The Great Gatsby"
    
    def test_search_exact_isbn_mockingbird(self):
        """
        Test: Exact ISBN search for "To Kill a Mockingbird"
        Expected: Should return exactly one book
        """
        result = search_books_in_catalog("9780061120084", "isbn")
        
        assert len(result) == 1
        assert result[0]['isbn'] == "9780061120084"
        assert result[0]['title'] == "To Kill a Mockingbird"
    
    def test_search_partial_isbn(self):
        """
        Test: Partial ISBN search "978074327"
        Expected: Should find "The Great Gatsby" (ISBN starts with this)
        """
        result = search_books_in_catalog("978074327", "isbn")
        
        assert len(result) == 1
        assert "978074327" in result[0]['isbn']
        assert result[0]['title'] == "The Great Gatsby"
    
    def test_search_nonexistent_isbn(self):
        """
        Test: Search for ISBN that doesn't exist
        Expected: Should return empty list
        """
        result = search_books_in_catalog("9999999999999", "isbn")
        
        assert len(result) == 0


    # Aadded from A2
    
    def setup_method(self):
        """Setup test data for multiple results"""
        from database import get_db_connection
        conn = get_db_connection()
        # Add books with similar titles/authors for testing multiple results
        conn.execute('''
            INSERT INTO books (title, author, isbn, total_copies, available_copies)
            VALUES 
            ("The Book of Python", "John Smith", "1111111111111", 1, 1),
            ("Python Programming", "John Smith", "2222222222222", 1, 1),
            ("Learning Python", "Jane Smith", "3333333333333", 1, 1)
        ''')
        conn.commit()
        conn.close()

    def test_search_multiple_title_matches(self):
        """
        Test: Search term matching multiple titles
        Expected: Should return all matching books sorted alphabetically
        """
        result = search_books_in_catalog("Python", "title")
        
        assert len(result) >= 3
        assert all("python" in book['title'].lower() for book in result)
        # Verify alphabetical sorting
        titles = [book['title'] for book in result]
        assert titles == sorted(titles)

    def test_search_multiple_author_matches(self):
        """
        Test: Search for author with multiple books
        Expected: Should return all books by author
        """
        result = search_books_in_catalog("Smith", "author")
        
        assert len(result) >= 3
        assert all("smith" in book['author'].lower() for book in result)

    def test_search_with_special_characters(self):
        """
        Test: Search with special characters and spaces
        Expected: Should handle special characters appropriately
        """
        result = search_books_in_catalog("Book & Python!", "title")
        
        assert isinstance(result, list)
        assert any("Book of Python" in book['title'] for book in result)

    def test_search_with_unicode_characters(self):
        """
        Test: Search with Unicode characters
        Expected: Should handle Unicode characters appropriately
        """
        # Add a book with Unicode characters
        from database import get_db_connection
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO books (title, author, isbn, total_copies, available_copies)
            VALUES ("El Código Python", "José García", "4444444444444", 1, 1)
        ''')
        conn.commit()
        conn.close()

        result = search_books_in_catalog("código", "title")
        assert len(result) >= 1
        assert any("Código" in book['title'] for book in result)

class TestSearchBooksEdgeCases:
    """Test search functionality edge cases"""

    def test_search_very_long_search_term(self):
        """
        Test: Search with very long search term
        Expected: Should handle gracefully
        """
        long_term = "a" * 500
        result = search_books_in_catalog(long_term, "title")
        
        assert isinstance(result, list)

    def test_search_with_sql_injection_attempt(self):
        """
        Test: Search with SQL injection attempt
        Expected: Should handle safely
        """
        malicious_input = "'; DROP TABLE books; --"
        result = search_books_in_catalog(malicious_input, "title")
        
        assert isinstance(result, list)
        # Verify database is still intact
        all_books = search_books_in_catalog("", "title")
        assert len(all_books) > 0

    def test_search_mixed_type(self):
        """
        Test: Search with numeric and text mixed
        Expected: Should handle mixed content appropriately
        """
        result = search_books_in_catalog("Python 3", "title")
        assert isinstance(result, list)

    def test_search_results_structure(self):
        """
        Test: Verify search results contain all required fields
        Expected: Each result should have all catalog display fields
        """
        result = search_books_in_catalog("Python", "title")
        required_fields = ['id', 'title', 'author', 'isbn', 'total_copies', 'available_copies']
        
        for book in result:
            assert all(field in book for field in required_fields)
            assert isinstance(book['id'], int)
            assert isinstance(book['total_copies'], int)
            assert isinstance(book['available_copies'], int)

class TestSearchPerformance:
    """Test search functionality performance with large dataset"""

    def setup_method(self):
        """Setup large dataset for performance testing"""
        from database import get_db_connection
        conn = get_db_connection()
        # Add 100 sample books
        for i in range(100):
            conn.execute('''
                INSERT INTO books (title, author, isbn, total_copies, available_copies)
                VALUES (?, ?, ?, 1, 1)
            ''', (
                f"Test Book {i}",
                f"Author {i}",
                f"{str(i).zfill(13)}"
            ))
        conn.commit()
        conn.close()

    def test_search_large_dataset(self):
        """
        Test: Search performance with large dataset
        Expected: Should return results quickly and correctly
        """
        import time
        start_time = time.time()
        
        result = search_books_in_catalog("Test", "title")
        
        end_time = time.time()
        search_time = end_time - start_time
        
        assert len(result) >= 100  # Should find all test books
        assert search_time < 1.0  # Should complete within 1 second