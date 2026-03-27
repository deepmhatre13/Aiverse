import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements
} from '@stripe/react-stripe-js';
import {
  CreditCard,
  Lock,
  Check,
  Loader2,
  X,
  Shield,
  AlertCircle,
  ExternalLink,
  Zap,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import api from '@/api/axios';
import { toast } from 'sonner';

// Initialize Stripe with publishable key from environment
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '');

/**
 * Payment Form Component - Uses Stripe Elements
 * Handles payment confirmation with client_secret from backend
 */
function PaymentForm({ clientSecret, amount, currency, courseTitle, onSuccess, onClose }) {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Confirm payment with Stripe
      const { error: confirmError, paymentIntent } = await stripe.confirmCardPayment(
        clientSecret,
        {
          payment_method: {
            card: elements.getElement(CardElement),
          },
        }
      );

      if (confirmError) {
        setError(confirmError.message || 'Payment failed. Please try again.');
        setIsProcessing(false);
        return;
      }

      if (paymentIntent.status === 'succeeded') {
        // Payment succeeded - backend webhook will activate enrollment
        toast.success('Payment successful! Your enrollment will be activated shortly.');
        onSuccess();
      } else if (paymentIntent.status === 'requires_action') {
        // 3D Secure or other action required
        setError('Additional authentication required. Please complete the verification.');
        setIsProcessing(false);
      } else {
        setError('Payment was not completed. Please try again.');
        setIsProcessing(false);
      }
    } catch (err) {
      setError(err.message || 'An error occurred during payment. Please try again.');
      setIsProcessing(false);
    }
  };

  // Stripe Card Element styling
  const cardElementOptions = {
    style: {
      base: {
        fontSize: '16px',
        color: '#1a1a2e',
        fontFamily: 'Inter, system-ui, sans-serif',
        '::placeholder': {
          color: '#9ca3af',
        },
      },
      invalid: {
        color: '#ef4444',
        iconColor: '#ef4444',
      },
    },
    hidePostalCode: true,
  };

  // Format currency
  const formatPrice = (amt, curr = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: curr,
      minimumFractionDigits: 0,
    }).format(amt);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Course Summary */}
      <div className="p-4 bg-muted/50 rounded-lg border border-border">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-foreground truncate">{courseTitle}</h3>
            <p className="text-sm text-muted-foreground">Lifetime access</p>
          </div>
          <span className="text-2xl font-bold text-primary shrink-0 ml-4">
            {formatPrice(amount, currency)}
          </span>
        </div>
        
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Check className="h-4 w-4 text-emerald-500 shrink-0" />
            Full course access
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Check className="h-4 w-4 text-emerald-500 shrink-0" />
            Certificate of completion
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Check className="h-4 w-4 text-emerald-500 shrink-0" />
            Lifetime updates
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Check className="h-4 w-4 text-emerald-500 shrink-0" />
            30-day money-back guarantee
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-start gap-2">
          <AlertCircle className="h-4 w-4 text-destructive mt-0.5 shrink-0" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Card Element */}
      <div className="space-y-2">
        <Label htmlFor="card-element" className="text-sm font-medium">
          Card Details
        </Label>
        <div className="p-4 border border-border rounded-lg bg-background hover:border-primary/50 transition-colors">
          <CardElement
            id="card-element"
            options={cardElementOptions}
          />
        </div>
        <p className="text-xs text-muted-foreground flex items-center gap-1">
          <Lock className="h-3 w-3" />
          Your card information is securely processed by Stripe
        </p>
      </div>

      {/* Security Badge */}
      <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <Shield className="h-4 w-4" />
        Secured by Stripe • 256-bit SSL encryption
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={onClose}
          className="flex-1"
          disabled={isProcessing}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={!stripe || isProcessing}
          className="flex-1 bg-primary hover:bg-primary/90"
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Lock className="h-4 w-4 mr-2" />
              Pay {formatPrice(amount, currency)}
            </>
          )}
        </Button>
      </div>
    </form>
  );
}

/**
 * Main Stripe Payment Modal Component
 * 
 * Supports two payment flows:
 * 1. PaymentIntent (Stripe Elements) - Default, more control
 * 2. Checkout Session - Redirect to Stripe hosted page
 */
const StripePaymentModal = ({
  isOpen,
  onClose,
  course,
  clientSecret: providedClientSecret,
  onSuccess,
  useCheckout = false, // Set true to use Checkout Session instead
}) => {
  const [step, setStep] = useState('payment'); // payment, processing, success, checkout
  const [isCreatingIntent, setIsCreatingIntent] = useState(false);
  const [paymentData, setPaymentData] = useState(null);
  const [error, setError] = useState(null);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen && course) {
      setStep('payment');
      setError(null);
      
      if (providedClientSecret) {
        // Use provided client secret
        setPaymentData({
          client_secret: providedClientSecret,
          amount: parseFloat(course.price || 0),
          currency: course.currency || 'USD',
        });
      } else if (!paymentData && !useCheckout) {
        // Create payment intent
        createPaymentIntent();
      }
    }
  }, [isOpen, course, providedClientSecret, useCheckout]);

  const createPaymentIntent = async () => {
    if (!course?.slug) return;

    setIsCreatingIntent(true);
    setError(null);

    try {
      const response = await api.post('/api/learn/payments/create-intent/', {
        course_slug: course.slug,
      });

      setPaymentData({
        client_secret: response.data.client_secret,
        amount: response.data.amount,
        currency: response.data.currency || 'USD',
      });
    } catch (err) {
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.message || 
                          'Failed to initialize payment. Please try again.';
      setError(errorMessage);
      
      if (err.response?.status === 401 || err.response?.status === 403) {
        toast.error('Please login to purchase courses');
      } else {
        toast.error(errorMessage);
      }
    } finally {
      setIsCreatingIntent(false);
    }
  };

  const createCheckoutSession = async () => {
    if (!course?.slug) return;

    setStep('processing');
    setError(null);

    try {
      const response = await api.post('/api/learn/payments/create-checkout-session/', {
        course_slug: course.slug,
        success_url: `${window.location.origin}/learn/courses/${course.slug}?payment=success`,
        cancel_url: `${window.location.origin}/learn/courses/${course.slug}?payment=cancelled`,
      });

      // Redirect to Stripe Checkout
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      } else if (response.data.session_id) {
        // Use Stripe.js to redirect
        const stripe = await stripePromise;
        const { error } = await stripe.redirectToCheckout({
          sessionId: response.data.session_id,
        });
        if (error) {
          throw new Error(error.message);
        }
      }
    } catch (err) {
      setStep('payment');
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.message || 
                          'Failed to create checkout session. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    }
  };

  const handleSuccess = () => {
    setStep('success');
    // Wait a moment then close and trigger callback
    setTimeout(() => {
      if (onSuccess) onSuccess();
      handleClose();
    }, 2500);
  };

  const handleClose = () => {
    // Reset state when closing
    setStep('payment');
    setPaymentData(null);
    setError(null);
    onClose();
  };

  const retryPayment = () => {
    setError(null);
    if (useCheckout) {
      createCheckoutSession();
    } else {
      createPaymentIntent();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) handleClose(); }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-primary" />
            {step === 'success' ? 'Payment Successful' : 'Complete Purchase'}
          </DialogTitle>
        </DialogHeader>

        {/* Payment Step - Elements Form */}
        {step === 'payment' && !useCheckout && (
          <>
            {isCreatingIntent && (
              <div className="py-12 text-center">
                <Loader2 className="h-12 w-12 mx-auto mb-4 animate-spin text-primary" />
                <h3 className="font-semibold mb-2">Initializing Payment</h3>
                <p className="text-sm text-muted-foreground">
                  Setting up secure payment...
                </p>
              </div>
            )}

            {error && !isCreatingIntent && (
              <div className="py-6">
                <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-center">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2 text-destructive" />
                  <p className="text-sm text-destructive mb-4">{error}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={retryPayment}
                    className="w-full"
                  >
                    Try Again
                  </Button>
                </div>
              </div>
            )}

            {paymentData && !isCreatingIntent && !error && (
              <Elements stripe={stripePromise}>
                <PaymentForm
                  clientSecret={paymentData.client_secret}
                  amount={paymentData.amount}
                  currency={paymentData.currency}
                  courseTitle={course?.title || 'Course'}
                  onSuccess={handleSuccess}
                  onClose={handleClose}
                />
              </Elements>
            )}

            {!paymentData && !isCreatingIntent && !error && (
              <div className="py-12 text-center">
                <Loader2 className="h-8 w-8 mx-auto mb-4 animate-spin text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  Loading payment form...
                </p>
              </div>
            )}
          </>
        )}

        {/* Payment Step - Checkout Option */}
        {step === 'payment' && useCheckout && (
          <div className="py-6 space-y-6">
            <div className="p-4 bg-muted/50 rounded-lg border border-border text-center">
              <h3 className="font-semibold mb-1">{course?.title}</h3>
              <p className="text-3xl font-bold text-primary">
                ${parseFloat(course?.price || 0).toFixed(0)}
              </p>
              <p className="text-sm text-muted-foreground mt-1">One-time payment</p>
            </div>

            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                <p className="text-sm text-destructive text-center">{error}</p>
              </div>
            )}

            <Button
              onClick={createCheckoutSession}
              className="w-full h-12 bg-primary hover:bg-primary/90"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Checkout with Stripe
            </Button>

            <Button
              variant="outline"
              onClick={handleClose}
              className="w-full"
            >
              Cancel
            </Button>

            <p className="text-xs text-muted-foreground text-center">
              You'll be redirected to Stripe's secure checkout page
            </p>
          </div>
        )}

        {/* Processing Step */}
        {step === 'processing' && (
          <div className="py-12 text-center">
            <Loader2 className="h-12 w-12 mx-auto mb-4 animate-spin text-primary" />
            <h3 className="font-semibold mb-2">Redirecting to Checkout</h3>
            <p className="text-sm text-muted-foreground">
              Please wait while we redirect you to Stripe...
            </p>
          </div>
        )}

        {/* Success Step */}
        {step === 'success' && (
          <div className="py-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/10 flex items-center justify-center">
              <Check className="h-8 w-8 text-emerald-500" />
            </div>
            <h3 className="font-semibold mb-2 text-lg">Payment Successful!</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Your enrollment will be activated shortly.
            </p>
            <div className="flex items-center justify-center gap-2 text-xs text-emerald-600">
              <Zap className="h-3 w-3" />
              Activating course access...
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default StripePaymentModal;
