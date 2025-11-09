class PaymentGateway:
    def process_payment(self, patron_id: str, amount: float) -> dict:
        """
        Simulate processing a payment.

        Raises:
            ValueError: if amount is invalid.
        """
        if amount is None or amount <= 0:
            raise ValueError("Invalid payment amount.")
        if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
            raise ValueError("Invalid patron ID for payment.")
        return {
            "success": True,
            "message": f"Processed ${amount:.2f} for patron {patron_id}.",
        }
    

    def refund_payment(self, patron_id: str, amount: float) -> dict:
        """
        Simulate refunding a payment.

        Raises:
            ValueError: if amount is invalid.
        """
        if amount is None or amount <= 0:
            raise ValueError("Invalid refund amount.")
        if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
            raise ValueError("Invalid patron ID for refund.")
        return {
            "success": True,
            "message": f"Refunded ${amount:.2f} to patron {patron_id}.",
        }
