import { useState } from 'react';
import { AlertCircle, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { validateSocialUrl, getPlaceholder } from '../../lib/urlUtils';

const PLATFORM_INFO = {
  github: {
    title: 'GitHub Profile',
    description: 'Add your GitHub profile to showcase your repositories',
  },
  linkedin: {
    title: 'LinkedIn Profile',
    description: 'Add your LinkedIn profile to connect professionally',
  },
  portfolio: {
    title: 'Portfolio Website',
    description: 'Add your personal website or portfolio',
  },
};

export default function SocialEditModal({
  isOpen,
  onClose,
  socialType,
  currentUrl,
  onSave,
  isLoading = false,
}) {
  const [url, setUrl] = useState(currentUrl || '');
  const [error, setError] = useState('');
  const [touched, setTouched] = useState(false);

  const handleInputChange = (e) => {
    setUrl(e.target.value);
    setError('');
  };

  const handleSave = () => {
    setTouched(true);

    if (!url.trim()) {
      setError('URL is required');
      return;
    }

    const validation = validateSocialUrl(socialType, url);
    if (!validation.valid) {
      setError(validation.error);
      return;
    }

    onSave(url);
  };

  const handleRemove = () => {
    onSave(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !isLoading) {
      handleSave();
    }
    if (e.key === 'Escape') {
      onClose();
    }
  };

  const info = PLATFORM_INFO[socialType];
  const placeholder = getPlaceholder(socialType);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{info?.title}</DialogTitle>
          <DialogDescription>{info?.description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Input Field */}
          <div className="space-y-2">
            <label htmlFor="social-url" className="text-sm font-medium text-gray-900 dark:text-foreground">
              Profile URL
            </label>
            <Input
              id="social-url"
              type="url"
              placeholder={placeholder}
              value={url}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              className="font-mono text-sm"
              autoFocus
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-start gap-3 p-3 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/50 rounded-lg">
              <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400 mt-0.5 shrink-0" />
              <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
            </div>
          )}

          {/* Helper Text */}
          <p className="text-xs text-gray-600 dark:text-gray-400">
            {socialType === 'github' && 'Example: https://github.com/deepmhatre13'}
            {socialType === 'linkedin' && 'Example: https://linkedin.com/in/deepam-mhatre'}
            {socialType === 'portfolio' && 'Your personal website or portfolio URL'}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 justify-end">
          {currentUrl && (
            <Button
              variant="ghost"
              onClick={handleRemove}
              disabled={isLoading}
              className="mr-auto text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Remove
            </Button>
          )}
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isLoading} className="gap-2">
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save'
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
