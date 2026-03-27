/**
 * Purchase Modal - Razorpay + Stripe support
 *
 * Tries Razorpay first when VITE_RAZORPAY_KEY_ID is set.
 * Falls back to Stripe Checkout when Stripe is configured.
 */

import { useState, useEffect } from 'react';
import { CreditCard, Loader2, Check, AlertCircle, Shield } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { learnAPI } from '@/api/learn';
import { toast } from 'sonner';
import { formatINR } from '@/lib/currency';

const RAZORPAY_KEY = import.meta.env.VITE_RAZORPAY_KEY_ID || '';

function getThrottleMessage(err) {
  const retryAfterHeader = err?.response?.headers?.['retry-after'];
  const retryAfterSeconds = Number.parseInt(retryAfterHeader, 10);

  if (Number.isFinite(retryAfterSeconds) && retryAfterSeconds >= 86400) {
    return 'Too many payment attempts. Please come back after 1 day.';
  }

  return 'Too many payment attempts. Please come back after 1 hour.';
}

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = resolve;
    document.body.appendChild(script);
  });
}

export default function PurchaseModal({
  isOpen,
  onClose,
  course,
  onSuccess,
}) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [orderData, setOrderData] = useState(null);

  useEffect(() => {
    if (!isOpen || !course?.slug) {
      setOrderData(null);
      setError(null);
      return;
    }

    const createOrder = async () => {
      setIsProcessing(true);
      setError(null);
      try {
        const data = await learnAPI.createRazorpayOrder(course.slug);
        if (data?.order_id && data?.key_id) {
          setOrderData(data);
        } else {
          setOrderData({ useStripe: true });
        }
      } catch (err) {
        if (err.response?.status === 503) {
          setOrderData({ useStripe: true });
          setError(null);
        } else if (err.response?.status === 429) {
          const msg = getThrottleMessage(err);
          setError(msg);
          toast.error(msg);
        } else {
          const msg =
            err.response?.data?.message ||
            err.response?.data?.error ||
            err.message ||
            'Failed to initialize payment';
          setError(msg);
          if (err.response?.status !== 401) {
            toast.error(msg);
          }
        }
      } finally {
        setIsProcessing(false);
      }
    };

    createOrder();
  }, [isOpen, course?.slug]);

  const handleRazorpayPay = async () => {
    if (!orderData?.order_id || !window.Razorpay) return;

    await loadRazorpayScript();

    const options = {
      key: orderData.key_id,
      amount: orderData.amount,
      currency: orderData.currency || 'INR',
      order_id: orderData.order_id,
      name: 'AiVerse',
      description: course?.title || 'Course Purchase',
      handler: async (res) => {
        setIsProcessing(true);
        setError(null);
        try {
          await learnAPI.verifyRazorpayPayment({
            order_id: res.razorpay_order_id,
            payment_id: res.razorpay_payment_id,
            signature: res.razorpay_signature,
            course_slug: course.slug,
          });
          toast.success('Payment successful!');
          onSuccess?.();
          onClose();
        } catch (err) {
          const msg =
            err.response?.data?.message ||
            err.response?.data?.error ||
            'Payment verification failed';
          setError(msg);
          toast.error(msg);
        } finally {
          setIsProcessing(false);
        }
      },
      prefill: {
        email: '',
        contact: '',
      },
      theme: {
        color: '#E10600',
      },
    };

    try {
      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', (res) => {
        setError(res.error?.description || 'Payment failed');
        toast.error('Payment failed. Please try again.');
      });
      rzp.open();
    } catch (err) {
      setError(err.message || 'Failed to open payment');
      toast.error('Failed to open payment');
    }
  };

  const handleStripeCheckout = async () => {
    setIsProcessing(true);
    setError(null);
    try {
      const url = `${window.location.origin}/learn/courses/${course.slug}`;
      const data = await learnAPI.createStripeCheckout(
        course.slug,
        `${url}?payment=success`,
        `${url}?payment=cancelled`
      );
      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        throw new Error('No checkout URL');
      }
    } catch (err) {
      const msg =
        err.response?.data?.message ||
        err.response?.data?.error ||
        'Failed to create checkout';
      setError(msg);
      toast.error(msg);
    } finally {
      setIsProcessing(false);
    }
  };

  const price = parseFloat(course?.price || 0);
  const formatPrice = (amt) => formatINR(amt);

  const handlePay = () => {
    if (orderData?.useStripe) {
      handleStripeCheckout();
    } else if (orderData?.order_id) {
      handleRazorpayPay();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-md dark">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-primary" />
            Complete Purchase
          </DialogTitle>
          <DialogDescription>
            Secure payment for lifetime access to this course.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <div className="p-4 rounded-xl border border-primary/20 bg-primary/5">
            <h3 className="font-semibold text-foreground truncate mb-1">
              {course?.title}
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Lifetime access • Certificate • Updates
            </p>
            <div className="text-2xl font-bold text-primary">
              {formatPrice(price)}
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg border border-destructive/30 bg-destructive/10 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          {isProcessing && !orderData ? (
            <div className="py-8 text-center">
              <Loader2 className="h-10 w-10 mx-auto mb-3 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                Initializing payment...
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <Button
                onClick={handlePay}
                disabled={isProcessing || !orderData}
                className="w-full h-12 bg-primary hover:bg-primary/90"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4 mr-2" />
                    Pay {formatPrice(price)}
                  </>
                )}
              </Button>
              <Button variant="outline" onClick={onClose} className="w-full">
                Cancel
              </Button>
            </div>
          )}

          <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <Shield className="h-4 w-4" />
            Secured payment • 256-bit SSL
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
