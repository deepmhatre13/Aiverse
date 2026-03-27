import React, { useState } from 'react';
import { CreditCard, Lock, Check, Loader2, X, Shield } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import api from '@/api/axios';

const PaymentModal = ({ 
  isOpen, 
  onClose, 
  course,
  onSuccess 
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [step, setStep] = useState('details'); // details, processing, success
  const [error, setError] = useState(null);

  const handlePayment = async () => {
    setIsProcessing(true);
    setError(null);
    setStep('processing');

    try {
      const response = await api.post('/api/learn/payments/create-intent/', {
        course_id: course?.id,
        course_slug: course?.slug,
      });

      // Redirect to Stripe checkout if URL provided
      if (response.data?.checkout_url) {
        window.location.href = response.data.checkout_url;
        return;
      }

      // Otherwise show success
      setStep('success');
      setTimeout(() => {
        if (onSuccess) onSuccess();
        onClose();
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.message || 'Payment failed. Please try again.');
      setStep('details');
    } finally {
      setIsProcessing(false);
    }
  };

  const resetModal = () => {
    setStep('details');
    setError(null);
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) { resetModal(); onClose(); } }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-primary" />
            {step === 'success' ? 'Payment Successful' : 'Complete Purchase'}
          </DialogTitle>
        </DialogHeader>

        {step === 'details' && (
          <div className="space-y-6">
            {/* Course Summary */}
            <div className="p-4 bg-muted/50 rounded-lg border border-border">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-semibold">{course?.title || 'Premium Course'}</h3>
                  <p className="text-sm text-muted-foreground">
                    {course?.lessons_count || 0} lessons • Lifetime access
                  </p>
                </div>
                <span className="text-2xl font-bold text-primary">
                  ${course?.price || 49}
                </span>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Check className="h-4 w-4 text-green-500" />
                  Full course access
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Check className="h-4 w-4 text-green-500" />
                  Certificate of completion
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Check className="h-4 w-4 text-green-500" />
                  Lifetime updates
                </div>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {/* Payment Form Preview */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input 
                  id="email" 
                  type="email" 
                  placeholder="your@email.com"
                  className="bg-background"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="card">Card Details</Label>
                <div className="relative">
                  <Input 
                    id="card" 
                    placeholder="•••• •••• •••• ••••"
                    className="bg-background pl-10"
                  />
                  <CreditCard className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="expiry">Expiry</Label>
                  <Input 
                    id="expiry" 
                    placeholder="MM/YY"
                    className="bg-background"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cvc">CVC</Label>
                  <Input 
                    id="cvc" 
                    placeholder="•••"
                    className="bg-background"
                  />
                </div>
              </div>
            </div>

            {/* Security Badge */}
            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <Shield className="h-3 w-3" />
              Secured by Stripe • 256-bit encryption
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <Button 
                variant="outline" 
                onClick={onClose}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button 
                onClick={handlePayment}
                disabled={isProcessing}
                className="flex-1 bg-primary hover:bg-primary/90"
              >
                <Lock className="h-4 w-4 mr-2" />
                Pay ${course?.price || 49}
              </Button>
            </div>
          </div>
        )}

        {step === 'processing' && (
          <div className="py-12 text-center">
            <Loader2 className="h-12 w-12 mx-auto mb-4 animate-spin text-primary" />
            <h3 className="font-semibold mb-2">Processing Payment</h3>
            <p className="text-sm text-muted-foreground">
              Please wait while we process your payment...
            </p>
          </div>
        )}

        {step === 'success' && (
          <div className="py-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-500/10 flex items-center justify-center">
              <Check className="h-8 w-8 text-green-500" />
            </div>
            <h3 className="font-semibold mb-2">Payment Successful!</h3>
            <p className="text-sm text-muted-foreground">
              You now have full access to {course?.title || 'this course'}
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default PaymentModal;
