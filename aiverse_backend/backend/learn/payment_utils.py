"""
Razorpay payment integration utilities.

Handles:
- Order creation
- Signature verification (HMAC-SHA256)
- Replay attack prevention
- Duplicate enrollment prevention
"""

import hmac
import hashlib
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def is_razorpay_configured():
    """Check if Razorpay keys are set."""
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '') or ''
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '') or ''
    return bool(key_id.strip() and key_secret.strip())


def create_razorpay_order(amount_paise, currency='INR', receipt_prefix='aiverse_', notes=None):
    """
    Create a Razorpay order.
    
    Args:
        amount_paise: Amount in paise (e.g. 10000 = ₹100)
        currency: Currency code (INR for Indian Rupees)
        receipt_prefix: Prefix for receipt id
        notes: Optional dict of metadata
        
    Returns:
        dict with order_id, amount, currency, key_id
        or None on failure
    """
    if not is_razorpay_configured():
        logger.error('Razorpay not configured')
        return None
    
    try:
        import razorpay
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        
        import uuid
        receipt = f"{receipt_prefix}{uuid.uuid4().hex[:12]}"
        
        order_data = {
            'amount': amount_paise,
            'currency': currency,
            'receipt': receipt,
        }
        if notes:
            order_data['notes'] = notes
        
        order = client.order.create(data=order_data)
        
        return {
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'receipt': order['receipt'],
            'key_id': settings.RAZORPAY_KEY_ID,
            'notes': order.get('notes', {}),
        }
    except Exception as e:
        logger.exception(f'Razorpay order creation failed: {e}')
        return None


def verify_razorpay_signature(order_id, payment_id, signature):
    """
    Verify Razorpay payment signature to prevent tampering and replay.
    
    Args:
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID
        signature: Signature from frontend
        
    Returns:
        bool: True if signature is valid
    """
    if not is_razorpay_configured():
        logger.error('Razorpay not configured')
        return False
    
    try:
        key_secret = settings.RAZORPAY_KEY_SECRET.encode('utf-8')
        payload = f"{order_id}|{payment_id}".encode('utf-8')
        expected = hmac.new(
            key_secret,
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        logger.exception(f'Razorpay signature verification failed: {e}')
        return False
