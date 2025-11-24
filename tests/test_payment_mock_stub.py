import pytest
from unittest.mock import Mock, patch
from services.payment_service import PaymentGateway
from datetime import datetime, timedelta


from services.payment_service import PaymentGateway
from services.library_service import pay_late_fees, refund_late_fee_payment
from services import library_service

# ---------------------------------------------------------------------
# STUBBING AND MOCKING TESTS FOR pay_late_fees()
# ---------------------------------------------------------------------

@patch('services.library_service.calculate_late_fee_for_book')
@patch('services.library_service.get_book_by_id')
def test_pay_late_fees_success(mock_get_book, mock_calc_fee):
    """Test successful payment with stubs for database functions"""
    # Stub database functions
    mock_get_book.return_value = {
        'id': 1,
        'title': 'Test Book',
        'author': 'Test Author',
        'available_copies': 5
    }
    mock_calc_fee.return_value = {
        'fee_amount': 5.00,
        'days_overdue': 10,
        'status': 'Late fee calculated'
    }
    
    # Mock payment gateway
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = {
        "success": True, 
        "message": "Processed $5.00 for patron 123456."
    }
    
    from services.library_service import pay_late_fees
    
    # Execute test with mocked gateway
    result = pay_late_fees("123456", 1, mock_gateway)
    
    # Verify mock was called correctly
    mock_gateway.process_payment.assert_called_once_with("123456", 5.00)
    assert result["success"] is True
    assert "5.00" in result["message"]


@patch('services.library_service.calculate_late_fee_for_book')
@patch('services.library_service.get_book_by_id')
def test_pay_late_fees_declined(mock_get_book, mock_calc_fee):
    """Test payment declined by gateway"""
    # Stub database functions
    mock_get_book.return_value = {
        'id': 1,
        'title': 'Test Book',
        'author': 'Test Author'
    }
    mock_calc_fee.return_value = {
        'fee_amount': 5.00,
        'days_overdue': 10,
        'status': 'Late fee calculated'
    }
    
    # Mock payment gateway with declined payment
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.side_effect = ValueError("Payment declined")
    
    from services.library_service import pay_late_fees
    
    result = pay_late_fees("123456", 1, mock_gateway)
    
    mock_gateway.process_payment.assert_called_once_with("123456", 5.00)
    assert result["success"] is False
    assert "declined" in result["message"].lower()


@patch('services.library_service.calculate_late_fee_for_book')
@patch('services.library_service.get_book_by_id')
def test_pay_late_fees_invalid_patron_not_called(mock_get_book, mock_calc_fee):
    """Test invalid patron ID - mock should NOT be called"""
    # Stub database functions
    mock_get_book.return_value = {
        'id': 1,
        'title': 'Test Book'
    }
    mock_calc_fee.return_value = {
        'fee_amount': 0.00,
        'days_overdue': 0,
        'status': 'Invalid patron ID'
    }
    
    # Mock payment gateway
    mock_gateway = Mock(spec=PaymentGateway)
    
    from services.library_service import pay_late_fees
    
    result = pay_late_fees("INVALID", 1, mock_gateway)
    
    # Verify mock was NOT called due to invalid patron
    mock_gateway.process_payment.assert_not_called()
    assert result["success"] is False


@patch('services.library_service.calculate_late_fee_for_book')
@patch('services.library_service.get_book_by_id')
def test_pay_late_fees_zero_fees_not_called(mock_get_book, mock_calc_fee):
    """Test zero late fees - mock should NOT be called"""
    # Stub database functions to return no overdue fees
    mock_get_book.return_value = {
        'id': 1,
        'title': 'Test Book'
    }
    mock_calc_fee.return_value = {
        'fee_amount': 0.00,
        'days_overdue': 0,
        'status': 'Book not overdue'
    }
    
    # Mock payment gateway
    mock_gateway = Mock(spec=PaymentGateway)
    
    from services.library_service import pay_late_fees
    
    result = pay_late_fees("123456", 1, mock_gateway)
    
    # Verify mock was NOT called when fees are zero
    mock_gateway.process_payment.assert_not_called()
    assert result["success"] is False
    assert "no fees" in result["message"].lower() or "zero" in result["message"].lower() or "not overdue" in result["message"].lower()


@patch('services.library_service.calculate_late_fee_for_book')
@patch('services.library_service.get_book_by_id')
def test_pay_late_fees_network_error(mock_get_book, mock_calc_fee):
    """Test network error exception handling"""
    # Stub database functions
    mock_get_book.return_value = {
        'id': 1,
        'title': 'Test Book'
    }
    mock_calc_fee.return_value = {
        'fee_amount': 5.00,
        'days_overdue': 10,
        'status': 'Late fee calculated'
    }
    
    # Mock payment gateway with network error
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.side_effect = ConnectionError("Network failure")
    
    from services.library_service import pay_late_fees
    
    result = pay_late_fees("123456", 1, mock_gateway)
    
    mock_gateway.process_payment.assert_called_once_with("123456", 5.00)
    assert result["success"] is False
    assert "network" in result["message"].lower() or "connection" in result["message"].lower()


# ---------------------------------------------------------------------
# STUBBING AND MOCKING TESTS FOR refund_late_fee_payment()
# ---------------------------------------------------------------------

def test_refund_late_fee_success():
    """Test successful refund"""
    # Mock payment gateway
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = {
        "success": True,
        "message": "Refunded $5.00 to patron 123456."
    }
    
    from services.library_service import refund_late_fee_payment
    
    result = refund_late_fee_payment("TXN123456", 5.00, mock_gateway)
    
    mock_gateway.refund_payment.assert_called_once_with("TXN123456", 5.00)
    assert result["success"] is True
    assert "refunded" in result["message"].lower()


def test_refund_late_fee_invalid_transaction():
    """Test invalid transaction ID rejection"""
    # Mock payment gateway with invalid transaction
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = ValueError("Invalid transaction ID")
    
    from services.library_service import refund_late_fee_payment
    
    result = refund_late_fee_payment("INVALID", 5.00, mock_gateway)
    
    mock_gateway.refund_payment.assert_called_once_with("INVALID", 5.00)
    assert result["success"] is False
    assert "invalid" in result["message"].lower()


def test_refund_late_fee_negative_amount():
    """Test negative refund amount rejection"""
    # Mock payment gateway with negative amount error
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = ValueError("Invalid refund amount.")
    
    from services.library_service import refund_late_fee_payment
    
    result = refund_late_fee_payment("TXN123456", -5.00, mock_gateway)
    
    mock_gateway.refund_payment.assert_called_once_with("TXN123456", -5.00)
    assert result["success"] is False
    assert "invalid" in result["message"].lower()


def test_refund_late_fee_zero_amount():
    """Test zero refund amount rejection"""
    # Mock payment gateway with zero amount error
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = ValueError("Invalid refund amount.")
    
    from services.library_service import refund_late_fee_payment
    
    result = refund_late_fee_payment("TXN123456", 0.00, mock_gateway)
    
    mock_gateway.refund_payment.assert_called_once_with("TXN123456", 0.00)
    assert result["success"] is False


def test_refund_late_fee_exceeds_limit():
    """Test refund amount exceeding $15 maximum"""
    # Mock payment gateway with limit exceeded error
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = ValueError("Refund exceeds $15 limit.")
    
    from services.library_service import refund_late_fee_payment
    
    result = refund_late_fee_payment("TXN123456", 20.00, mock_gateway)
    
    mock_gateway.refund_payment.assert_called_once_with("TXN123456", 20.00)
    assert result["success"] is False
    assert "exceeds" in result["message"].lower() or "limit" in result["message"].lower()





# ---------------------------------------------------------------------
# DIRECT TESTS FOR PaymentGateway (to raise coverage)
# ---------------------------------------------------------------------

def test_process_payment_success():
    gateway = PaymentGateway()
    result = gateway.process_payment("123456", 10.0)
    assert result["success"] is True
    assert "Processed" in result["message"]

def test_process_payment_invalid_amount():
    gateway = PaymentGateway()
    with pytest.raises(ValueError, match="Invalid payment amount"):
        gateway.process_payment("123456", 0)

def test_process_payment_invalid_patron_id():
    gateway = PaymentGateway()
    with pytest.raises(ValueError, match="Invalid patron ID"):
        gateway.process_payment("ABCDEF", 10.0)

def test_refund_payment_success():
    gateway = PaymentGateway()
    result = gateway.refund_payment("123456", 5.0)
    assert result["success"] is True
    assert "Refunded" in result["message"]

def test_refund_payment_invalid_amount():
    gateway = PaymentGateway()
    with pytest.raises(ValueError, match="Invalid refund amount"):
        gateway.refund_payment("123456", -1.0)

def test_refund_payment_invalid_patron_id():
    gateway = PaymentGateway()
    with pytest.raises(ValueError, match="Invalid patron ID"):
        gateway.refund_payment("ABCDEF", 5.0)


# ---------------------------------------------------------------------
# EXTRA COVERAGE: library_service core branches via stubs/mocks
# ---------------------------------------------------------------------
# These target uncovered error / edge paths to push library_service.py
# over the 80% coverage requirement, without touching production code.
# ---------------------------------------------------------------------

def test_borrow_book_db_error_on_insert():
    """borrow_book_by_patron: branch where insert_borrow_record fails."""
    with patch("services.library_service.get_book_by_id",
               return_value={"id": 1, "title": "Test", "available_copies": 1}), \
         patch("services.library_service.get_patron_borrow_count",
               return_value=0), \
         patch("services.library_service.insert_borrow_record",
               return_value=False):
        success, msg = library_service.borrow_book_by_patron("123456", 1)

    assert success is False
    assert "creating borrow record" in msg.lower()


def test_borrow_book_db_error_on_availability_update():
    """borrow_book_by_patron: branch where update_book_availability fails."""
    with patch("services.library_service.get_book_by_id",
               return_value={"id": 1, "title": "Test", "available_copies": 1}), \
         patch("services.library_service.get_patron_borrow_count",
               return_value=0), \
         patch("services.library_service.insert_borrow_record",
               return_value=True), \
         patch("services.library_service.update_book_availability",
               return_value=False):
        success, msg = library_service.borrow_book_by_patron("123456", 1)

    assert success is False
    assert "updating book availability" in msg.lower()


def test_return_book_not_borrowed_by_patron():
    """return_book_by_patron: branch 'This book was not borrowed by this patron.'"""
    with patch("services.library_service.get_book_by_id",
               return_value={"id": 1, "title": "Test"}), \
         patch("services.library_service.get_patron_borrowed_books",
               return_value=[]):
        success, msg = library_service.return_book_by_patron("123456", 1)

    assert success is False
    assert "not borrowed" in msg.lower()


def test_return_book_db_error_on_update_record():
    """return_book_by_patron: branch where update_borrow_record_return_date fails."""
    borrowed = [{
        "book_id": 1,
        "due_date": datetime.now() - timedelta(days=1),
    }]
    with patch("services.library_service.get_book_by_id",
               return_value={"id": 1, "title": "Test"}), \
         patch("services.library_service.get_patron_borrowed_books",
               return_value=borrowed), \
         patch("services.library_service.update_borrow_record_return_date",
               return_value=False):
        success, msg = library_service.return_book_by_patron("123456", 1)

    assert success is False
    assert "updating return record" in msg.lower()


def test_return_book_db_error_on_availability_update():
    """return_book_by_patron: branch where update_book_availability fails on return."""
    borrowed = [{
        "book_id": 1,
        "due_date": datetime.now(),
    }]
    with patch("services.library_service.get_book_by_id",
               return_value={"id": 1, "title": "Test"}), \
         patch("services.library_service.get_patron_borrowed_books",
               return_value=borrowed), \
         patch("services.library_service.update_borrow_record_return_date",
               return_value=True), \
         patch("services.library_service.update_book_availability",
               return_value=False):
        success, msg = library_service.return_book_by_patron("123456", 1)

    assert success is False
    assert "updating book availability" in msg.lower()


def test_calculate_late_fee_book_not_borrowed():
    """calculate_late_fee_for_book: 'Book not borrowed by this patron' branch."""
    with patch("services.library_service.get_book_by_id",
               return_value={"id": 1}), \
         patch("services.library_service.get_patron_borrowed_books",
               return_value=[]):
        result = library_service.calculate_late_fee_for_book("123456", 1)

    assert result["fee_amount"] == 0.0
    assert result["status"] == "Book not borrowed by this patron"


def test_search_books_handles_exception():
    """search_books_in_catalog: exercise except-block returning [] on DB error."""

    class BadConn:
        def execute(self, *args, **kwargs):
            raise Exception("DB failure")

        def close(self):
            pass

    with patch("services.library_service.get_db_connection", return_value=BadConn()):
        results = library_service.search_books_in_catalog("anything", "title")

    assert results == []


def test_get_patron_status_report_db_error():
    """get_patron_status_report: exercise exception path -> error dict."""

    class BadConn:
        def execute(self, *args, **kwargs):
            raise Exception("DB failure")

        def close(self):
            pass

    with patch("services.library_service.get_db_connection", return_value=BadConn()), \
         patch("services.library_service.get_patron_borrowed_books",
               return_value=[]):
        report = library_service.get_patron_status_report("123456")

    assert report["error"].startswith("Database error occurred while generating report.")
    assert report["current_books"] == []