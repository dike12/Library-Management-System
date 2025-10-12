import pytest
import sys
sys.path.insert(0, '../')

from database import init_database
init_database()

from database import init_database, get_db_connection
from datetime import datetime, timedelta
from library_service import get_patron_status_report, borrow_book_by_patron

class TestPatronStatusReport:
    """Test suite for R7: Patron Status Report functionality"""
    
    def test_patron_status_empty_patron_id(self):
        """
        Test: Empty patron ID
        Expected: Should return error status
        """
        result = get_patron_status_report("")
        
        assert isinstance(result, dict)
        assert result.get('status') == 'error'
        assert 'invalid patron id' in result.get('message', '').lower()
    
    def test_patron_status_invalid_patron_id_length(self):
        """
        Test: Invalid patron ID length
        Expected: Should return error for non-6-digit patron ID
        """
        result = get_patron_status_report("12345")  # Too short
        assert isinstance(result, dict)
        assert result.get('status') == 'error'
        assert ('6 digits' in result.get('message', '').lower() or
                'invalid patron id' in result.get('message', '').lower())
    
    def test_patron_status_valid_patron_with_books(self):
        """
        Test: Valid patron ID with borrowed books
        Expected: Should return complete status report
        """
        # Use patron "123456" who should have borrowed book ID 3 from sample data
        result = get_patron_status_report("123456")
        
        assert isinstance(result, dict)
        assert result.get('status') == 'success'
        assert 'patron_id' in result
        assert result['patron_id'] == "123456"
        
        # Should contain required R7 fields
        assert 'currently_borrowed_books' in result
        assert 'total_late_fees_owed' in result
        assert 'number_of_books_borrowed' in result
        assert 'borrowing_history' in result
    
    def test_patron_status_valid_patron_no_books(self):
        """
        Test: Valid patron ID with no borrowed books
        Expected: Should return status report with zero values
        """
        result = get_patron_status_report("999999")  # Patron with no borrows
        
        assert isinstance(result, dict)
        assert result.get('status') == 'success'
        assert result.get('number_of_books_borrowed') == 0
        assert result.get('total_late_fees_owed') == 0.0
        assert len(result.get('currently_borrowed_books', [])) == 0
    
    def test_patron_status_currently_borrowed_structure(self):
        """
        Test: Currently borrowed books data structure
        Expected: Should contain books with due dates
        """
        result = get_patron_status_report("123456")
        
        if result.get('status') == 'success':
            borrowed_books = result.get('currently_borrowed_books', [])
            
            if len(borrowed_books) > 0:
                book = borrowed_books[0]
                assert isinstance(book, dict)
                
                # Should contain required book information
                required_fields = ['book_id', 'title', 'author', 'due_date']
                for field in required_fields:
                    assert field in book, f"Book should contain '{field}' field"
    
    def test_patron_status_total_late_fees(self):
        """
        Test: Total late fees owed calculation
        Expected: Should calculate sum of all late fees
        """
        result = get_patron_status_report("123456")
        
        if result.get('status') == 'success':
            late_fees = result.get('total_late_fees_owed')
            assert isinstance(late_fees, (int, float))
            assert late_fees >= 0, "Late fees should be non-negative"
    
    def test_patron_status_borrowing_history_structure(self):
        """
        Test: Borrowing history data structure
        Expected: Should contain all patron's borrowing records
        """
        result = get_patron_status_report("123456")
        
        if result.get('status') == 'success':
            history = result.get('borrowing_history', [])
            assert isinstance(history, list)
            
            if len(history) > 0:
                record = history[0]
                assert isinstance(record, dict)
                
                # Should contain borrowing record information
                expected_fields = ['book_id', 'title', 'author', 'borrow_date']
                for field in expected_fields:
                    assert field in record, f"History record should contain '{field}'"
    
    def test_patron_status_all_required_fields(self):
        """
        Test: Response contains all R7 required fields
        Expected: Should include all specified information
        """
        result = get_patron_status_report("123456")
        
        if result.get('status') == 'success':
            # R7 requirements
            required_fields = [
                'currently_borrowed_books',    # Currently borrowed books with due dates
                'total_late_fees_owed',        # Total late fees owed
                'number_of_books_borrowed',    # Number of books currently borrowed
                'borrowing_history'            # Borrowing history
            ]
            
            for field in required_fields:
                assert field in result, f"Status report must contain '{field}' field"
    
    def test_patron_status_response_format(self):
        """
        Test: Response is properly formatted dictionary
        Expected: Should be JSON-serializable for display
        """
        result = get_patron_status_report("123456")
        
        assert isinstance(result, dict)
        
        # Test JSON serializability
        import json
        try:
            json_str = json.dumps(result, default=str)  # default=str handles datetime
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result should be JSON serializable: {e}")
    
    def test_patron_status_invalid_parameter_types(self):
        """
        Test: Handle invalid parameter types
        Expected: Should handle gracefully
        """
        result = get_patron_status_report(123456)  # Integer instead of string
        
        assert isinstance(result, dict)
        assert result.get('status') == 'error'

    # Added from A2
    def setup_method(self):
        """Setup test environment before each test"""
        init_database()
        # Setup test data
        self._setup_test_data()
    
    def _setup_test_data(self):
        """Create test data for patron status testing"""
        # Create a patron with multiple borrowed books
        patron_id = "111111"
        borrow_book_by_patron(patron_id, 1)  # Borrow first book
        borrow_book_by_patron(patron_id, 2)  # Borrow second book
        
        # Create an overdue book scenario
        conn = get_db_connection()
        past_date = (datetime.now() - timedelta(days=20)).isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ?
        ''', (past_date, patron_id, 1))
        conn.commit()
        conn.close()

    def test_patron_status_valid_patron_comprehensive(self):
        """
        Positive test: Full patron status with borrowed and overdue books
        Expected: Complete status report with all required fields
        """
        result = get_patron_status_report("111111")
        
        assert result['status'] == 'success'
        assert len(result['currently_borrowed_books']) == 2
        assert result['total_late_fees_owed'] > 0
        assert result['number_of_books_borrowed'] == 2
        assert isinstance(result['borrowing_history'], list)

    def test_patron_status_borrowed_books_details(self):
        """
        Test: Verify borrowed books contain all required details
        Expected: Complete book information with due dates
        """
        result = get_patron_status_report("111111")
        
        for book in result['currently_borrowed_books']:
            assert all(key in book for key in ['book_id', 'title', 'author', 'due_date'])
            assert isinstance(book['due_date'], str)
            assert isinstance(book['book_id'], int)

    def test_patron_status_late_fees_calculation(self):
        """
        Test: Verify late fees are calculated correctly
        Expected: Accurate late fee calculation
        """
        result = get_patron_status_report("111111")
        
        assert isinstance(result['total_late_fees_owed'], (int, float))
        assert result['total_late_fees_owed'] <= 15.00  # Maximum per book
        assert result['total_late_fees_owed'] >= 0.00

    def test_patron_status_borrowing_history_complete(self):
        """
        Test: Verify borrowing history contains all transactions
        Expected: Complete borrowing history with details
        """
        result = get_patron_status_report("111111")
        
        assert isinstance(result['borrowing_history'], list)
        for record in result['borrowing_history']:
            assert all(key in record for key in [
                'book_id', 'title', 'author', 'borrow_date'
            ])
            assert isinstance(record['borrow_date'], str)

    def test_patron_status_json_structure(self):
        """
        Test: Verify JSON structure of response
        Expected: Well-formed JSON with all required fields
        """
        result = get_patron_status_report("111111")
        
        required_fields = [
            'status',
            'patron_id',
            'currently_borrowed_books',
            'total_late_fees_owed',
            'number_of_books_borrowed',
            'borrowing_history'
        ]
        
        assert all(field in result for field in required_fields)
        assert isinstance(result['currently_borrowed_books'], list)
        assert isinstance(result['borrowing_history'], list)

    def test_patron_status_no_borrowed_books(self):
        """
        Test: Patron with no borrowed books
        Expected: Empty lists and zero values
        """
        result = get_patron_status_report("999999")
        
        assert result['status'] == 'success'
        assert len(result['currently_borrowed_books']) == 0
        assert result['total_late_fees_owed'] == 0.00
        assert result['number_of_books_borrowed'] == 0
        assert len(result['borrowing_history']) == 0

    def test_patron_status_overdue_books_identification(self):
        """
        Test: Verify overdue books are properly identified
        Expected: Overdue status indicated in borrowed books
        """
        result = get_patron_status_report("111111")
        
        overdue_found = False
        for book in result['currently_borrowed_books']:
            if datetime.fromisoformat(book['due_date']) < datetime.now():
                overdue_found = True
                break
        
        assert overdue_found == True

    def test_patron_status_data_types(self):
        """
        Test: Verify correct data types in response
        Expected: All fields have correct data types
        """
        result = get_patron_status_report("111111")
        
        assert isinstance(result['patron_id'], str)
        assert isinstance(result['currently_borrowed_books'], list)
        assert isinstance(result['total_late_fees_owed'], (int, float))
        assert isinstance(result['number_of_books_borrowed'], int)
        assert isinstance(result['borrowing_history'], list)

    def test_patron_status_invalid_patron_format(self):
        """
        Negative test: Invalid patron ID format
        Expected: Error status with message
        """
        result = get_patron_status_report("12345")  # Too short
        
        assert result['status'] == 'error'
        assert 'invalid patron id' in result['message'].lower()

    def test_patron_status_special_characters(self):
        """
        Negative test: Patron ID with special characters
        Expected: Error status with message
        """
        result = get_patron_status_report("12@456")
        
        assert result['status'] == 'error'
        assert 'invalid patron id' in result['message'].lower()