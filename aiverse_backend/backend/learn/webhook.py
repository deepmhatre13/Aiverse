"""
Production-grade Stripe Webhook Handler.

Handles:
- checkout.session.completed (Checkout flow)
- payment_intent.succeeded (Elements flow)
- payment_intent.payment_failed
- charge.refunded

CRITICAL SECURITY:
- All webhooks verified with signature
- No frontend-based trust
- Backend verifies everything
"""

import stripe
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import Payment, Enrollment, Course

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle all Stripe webhook events.
    
    CRITICAL: Verify signature before processing.
    """
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    
    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        return HttpResponse(status=500)

    if not stripe.api_key:
        logger.error("STRIPE_SECRET_KEY not configured")
        return HttpResponse(status=500)
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload in Stripe webhook: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature in Stripe webhook: {e}")
        return HttpResponse(status=400)
    
    # Handle event types
    event_type = event['type']
    event_data = event['data']['object']
    
    handlers = {
        'checkout.session.completed': handle_checkout_completed,
        'payment_intent.succeeded': handle_payment_succeeded,
        'payment_intent.payment_failed': handle_payment_failed,
        'charge.refunded': handle_charge_refunded,
    }
    
    handler = handlers.get(event_type)
    if handler:
        try:
            handler(event_data)
            logger.info(f"Successfully handled Stripe webhook: {event_type}")
        except Exception as e:
            logger.error(f"Error handling {event_type}: {e}")
            # Return 200 to prevent Stripe retries for handled but failed events
            # Log error for investigation
            return HttpResponse(status=200)
    else:
        logger.debug(f"Unhandled Stripe webhook event: {event_type}")
    
    return HttpResponse(status=200)


def handle_checkout_completed(session):
    """
    Handle successful Checkout Session.
    
    Steps:
    1. Verify payment status
    2. Update Payment record
    3. Activate Enrollment
    4. Update Course stats
    5. (no receipt generation)
    """
    
    session_id = session['id']
    payment_status = session.get('payment_status')
    
    if payment_status != 'paid':
        logger.warning(f"Checkout completed but not paid: {session_id}")
        return
    
    # Extract metadata
    metadata = session.get('metadata', {})
    user_id = metadata.get('user_id')
    course_id = metadata.get('course_id')
    enrollment_id = metadata.get('enrollment_id')
    
    if not all([user_id, course_id, enrollment_id]):
        logger.error(f"Missing metadata in checkout session: {session_id}")
        return
    
    try:
        with transaction.atomic():
            # Find Payment record by checkout session ID
            payment = Payment.objects.select_for_update().filter(
                stripe_checkout_session_id=session_id
            ).first()
            
            if not payment:
                # Try by payment intent
                payment_intent_id = session.get('payment_intent')
                if payment_intent_id:
                    payment = Payment.objects.select_for_update().filter(
                        stripe_payment_intent_id=payment_intent_id
                    ).first()
            
            if not payment:
                logger.error(f"Payment not found for checkout session: {session_id}")
                return
            
            # Update payment
            payment.status = 'succeeded'
            payment.succeeded_at = timezone.now()
            if session.get('payment_intent'):
                payment.stripe_payment_intent_id = session['payment_intent']
            payment.save()
            
            # Activate enrollment
            enrollment = payment.enrollment
            enrollment.status = 'active'
            enrollment.is_paid = True
            enrollment.activated_at = timezone.now()
            enrollment.purchased_at = timezone.now()
            enrollment.amount_paid = payment.amount
            enrollment.payment_reference = payment.stripe_payment_intent_id
            enrollment.save()
            
            # Update course stats
            course = enrollment.course
            course.update_stats()
            
            logger.info(
                f"Checkout completed: session={session_id}, "
                f"user={payment.enrollment.user.email}, course={course.title}"
            )
            
    except Exception as e:
        logger.error(f"Error processing checkout completion: {e}")
        raise


def handle_payment_succeeded(payment_intent):
    """
    Handle successful PaymentIntent (Elements flow).
    
    Similar to checkout completion but for custom payment forms.
    """
    
    payment_intent_id = payment_intent['id']
    
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )
            
            # Skip if already processed
            if payment.status == 'succeeded':
                logger.info(f"Payment already processed: {payment_intent_id}")
                return
            
            # Update payment
            payment.status = 'succeeded'
            payment.succeeded_at = timezone.now()
            if payment_intent.get('latest_charge'):
                payment.stripe_charge_id = payment_intent['latest_charge']
            payment.save()
            
            # Activate enrollment
            enrollment = payment.enrollment
            enrollment.status = 'active'
            enrollment.is_paid = True
            enrollment.activated_at = timezone.now()
            enrollment.purchased_at = timezone.now()
            enrollment.amount_paid = payment.amount
            enrollment.save()
            
            # Update course stats
            course = enrollment.course
            course.update_stats()
            
            logger.info(
                f"Payment succeeded: {payment_intent_id}, "
                f"enrollment {enrollment.id} activated"
            )
            
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for intent: {payment_intent_id}")
    except Exception as e:
        logger.error(f"Error handling payment success: {e}")
        raise


def handle_payment_failed(payment_intent):
    """Handle failed PaymentIntent."""
    
    payment_intent_id = payment_intent['id']
    
    try:
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
        payment.status = 'failed'
        
        # Extract failure reason
        last_error = payment_intent.get('last_payment_error', {})
        payment.failure_reason = last_error.get('message', 'Payment failed')
        payment.save()
        
        logger.warning(
            f"Payment failed: {payment_intent_id}, "
            f"reason: {payment.failure_reason}"
        )
        
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for failed intent: {payment_intent_id}")


def handle_charge_refunded(charge):
    """
    Handle refunded charge.
    
    Steps:
    1. Find associated Payment
    2. Update Payment status
    3. Update Enrollment status
    4. Update Course stats
    """
    
    charge_id = charge['id']
    payment_intent_id = charge.get('payment_intent')
    
    if not payment_intent_id:
        logger.error(f"No payment_intent in refunded charge: {charge_id}")
        return
    
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )
            
            # Check if fully refunded
            if charge.get('refunded', False):
                payment.status = 'refunded'
                payment.save()
                
                # Update enrollment
                enrollment = payment.enrollment
                enrollment.status = 'refunded'
                enrollment.save()
                
                # Update course stats
                course = enrollment.course
                course.update_stats()
                
                logger.info(
                    f"Charge refunded: {charge_id}, "
                    f"enrollment {enrollment.id} refunded"
                )
            
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for refunded charge: {charge_id}")
    except Exception as e:
        logger.error(f"Error handling refund: {e}")
        raise
