import pytest
import sys
sys.path.insert(0, '../')

from database import init_database
init_database()


from library_service import calculate_late_fee_for_book

class TestLateFeeValidation:
    """Test patron ID and book ID validation"""
    
    def test_late_fee_empty_patron_id(self):
        """
        Test: Empty patron ID
        Expected: Should fail with validation error
        """
        result = calculate_late_fee_for_book("", 1)
        
        assert result['status'] == 'error'
        assert 'invalid patron id' in result.get('message', '').lower()
    
    def test_late_fee_invalid_patron_id_length(self):
        """
        Test: Invalid patron ID length
        Expected: Should fail with validation error
        """
        result = calculate_late_fee_for_book("12345", 1)  # Too short
        
        assert result['status'] == 'error'
        assert ('6 digits' in result.get('message', '').lower() or 
                'invalid patron id' in result.get('message', '').lower())
    
    def test_late_fee_patron_id_with_letters(self):
        """
        Test: Patron ID with non-digit characters
        Expected: Should fail with validation error
        """
        result = calculate_late_fee_for_book("12345A", 1)
        
        assert result['status'] == 'error'
        assert ('6 digits' in result.get('message', '').lower() or
                'invalid patron id' in result.get('message', '').lower())
    
    def test_late_fee_none_patron_id(self):
        """
        Test: None patron ID
        Expected: Should fail with validation error
        """
        result = calculate_late_fee_for_book(None, 1)
        
        assert result['status'] == 'error'
        assert ('invalid patron id' in result.get('message', '').lower() or
                'patron id is required' in result.get('message', '').lower())
    
    def test_late_fee_negative_book_id(self):
        """
        Test: Negative book ID
        Expected: Should fail with validation error
        """
        result = calculate_late_fee_for_book("123456", -1)
        
        assert result['status'] == 'error'
        assert ('book not found' in result.get('message', '').lower() or
                'invalid book id' in result.get('message', '').lower())
    
    def test_late_fee_zero_book_id(self):
        """
        Test: Zero book ID
        Expected: Should fail with validation error
        """
        result = calculate_late_fee_for_book("123456", 0)
        
        assert result['status'] == 'error'
        assert ('book not found' in result.get('message', '').lower() or
                'invalid book id' in result.get('message', '').lower())
        

    # Added from A2
    # ...existing code...

class TestLateFeeCalculation:
    """Test suite for R5: Late Fee Calculation functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup test environment before each test"""
        init_database()
        # Setup borrowed books for testing
        from library_service import borrow_book_by_patron
        from datetime import datetime, timedelta
        
        # Borrow books and manipulate due dates for testing
        borrow_book_by_patron("111111", 1)  # Will be 5 days overdue
        borrow_book_by_patron("222222", 2)  # Will be 10 days overdue
        
        # Adjust due dates in database
        conn = get_db_connection()
        five_days_overdue = (datetime.now() - timedelta(days=5)).isoformat()
        ten_days_overdue = (datetime.now() - timedelta(days=10)).isoformat()
        
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ?
        ''', (five_days_overdue, "111111", 1))
        
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ?
        ''', (ten_days_overdue, "222222", 2))
        
        conn.commit()
        conn.close()

    def test_no_late_fee_book_on_time(self):
        """
        Test: Book returned on time
        Expected: No late fee
        """
        from library_service import borrow_book_by_patron
        borrow_book_by_patron("333333", 3)  # Fresh borrow
        
        result = calculate_late_fee_for_book("333333", 3)
        
        assert result['status'] == 'success'
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0

    def test_late_fee_within_first_week(self):
        """
        Test: Book 5 days overdue (within first week)
        Expected: $0.50 per day fee
        """
        result = calculate_late_fee_for_book("111111", 1)
        
        assert result['status'] == 'success'
        assert result['days_overdue'] == 5
        assert result['fee_amount'] == 2.50  # 5 days * $0.50

    def test_late_fee_beyond_first_week(self):
        """
        Test: Book 10 days overdue (beyond first week)
        Expected: First week at $0.50/day + remaining days at $1.00/day
        """
        result = calculate_late_fee_for_book("222222", 2)
        
        assert result['status'] == 'success'
        assert result['days_overdue'] == 10
        assert result['fee_amount'] == 6.50  # (7 * $0.50) + (3 * $1.00)

    def test_late_fee_maximum_cap(self):
        """
        Test: Book overdue long enough to exceed maximum fee
        Expected: Fee capped at $15.00
        """
        conn = get_db_connection()
        thirty_days_overdue = (datetime.now() - timedelta(days=30)).isoformat()
        
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ?
        ''', (thirty_days_overdue, "222222", 2))
        conn.commit()
        conn.close()
        
        result = calculate_late_fee_for_book("222222", 2)
        
        assert result['status'] == 'success'
        assert result['days_overdue'] == 30
        assert result['fee_amount'] == 15.00  # Maximum cap

    def test_fee_for_non_borrowed_book(self):
        """
        Test: Calculate fee for book not borrowed by patron
        Expected: Error status
        """
        result = calculate_late_fee_for_book("444444", 1)
        
        assert result['status'] == 'error'
        assert 'not borrowed' in result['message'].lower()

    def test_fee_precision(self):
        """
        Test: Verify fee amount has exactly 2 decimal places
        Expected: Fee amount with correct precision
        """
        result = calculate_late_fee_for_book("111111", 1)
        
        assert result['status'] == 'success'
        assert isinstance(result['fee_amount'], float)
        assert str(result['fee_amount']).split('.')[-1] == '50'  # Verify 2 decimal places

    def test_multiple_overdue_books(self):
        """
        Test: Calculate fees for multiple overdue books
        Expected: Correct individual fees
        """
        result1 = calculate_late_fee_for_book("111111", 1)
        result2 = calculate_late_fee_for_book("222222", 2)
        
        assert result1['status'] == 'success' and result2['status'] == 'success'
        assert result1['fee_amount'] != result2['fee_amount']
        assert result1['days_overdue'] < result2['days_overdue']

    def test_returned_book_late_fee(self):
        """
        Test: Calculate fee for already returned book
        Expected: Error status
        """
        from library_service import return_book_by_patron
        return_book_by_patron("111111", 1)
        
        result = calculate_late_fee_for_book("111111", 1)
        
        assert result['status'] == 'error'
        assert 'not borrowed' in result['message'].lower()

    def test_future_due_date(self):
        """
        Test: Calculate fee for book not yet due
        Expected: Zero fee
        """
        from library_service import borrow_book_by_patron
        borrow_book_by_patron("555555", 3)  # Fresh borrow with future due date
        
        result = calculate_late_fee_for_book("555555", 3)
        
        assert result['status'] == 'success'
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0

    def test_fee_calculation_boundary_cases(self):
        """
        Test: Fee calculation at boundary conditions
        Expected: Correct fee amounts
        """
        conn = get_db_connection()
        
        # Test exactly 7 days overdue
        seven_days_overdue = (datetime.now() - timedelta(days=7)).isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ?
        ''', (seven_days_overdue, "111111", 1))
        conn.commit()
        
        result = calculate_late_fee_for_book("111111", 1)
        
        assert result['status'] == 'success'
        assert result['days_overdue'] == 7
        assert result['fee_amount'] == 3.50  # 7 days * $0.50