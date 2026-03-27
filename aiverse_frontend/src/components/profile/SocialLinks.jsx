import { useState, useCallback } from 'react';
import { Github, Linkedin, Globe, ExternalLink, Edit2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { Card, CardContent } from '../ui/card';
import SocialEditModal from './SocialEditModal';
import { getDisplayText, normalizeUrl } from '../../lib/urlUtils';
import { updateProfileSocial } from '../../api/profile';

const SOCIAL_CONFIG = {
  github: {
    icon: Github,
    label: 'GitHub',
    color: 'text-[#333]',
    emptyPlaceholder: 'Add GitHub profile',
  },
  linkedin: {
    icon: Linkedin,
    label: 'LinkedIn',
    color: 'text-[#0A66C2]',
    emptyPlaceholder: 'Add LinkedIn profile',
  },
  portfolio: {
    icon: Globe,
    label: 'Portfolio',
    color: 'text-[#3B82F6]',
    emptyPlaceholder: 'Add personal website',
  },
};

/**
 * SocialCard - Individual social link card
 * Shows connected state or empty state, with edit functionality
 */
function SocialCard({
  type,
  url,
  isLoading,
  onEdit,
  onOpenEdit,
}) {
  const config = SOCIAL_CONFIG[type];
  const Icon = config.icon;
  const displayText = getDisplayText(type, url);
  const isConnected = !!url;

  const handleCardClick = (e) => {
    if (isConnected && url) {
      // If clicking the external link icon, always open the link
      if (e.target.closest('[data-action="open-link"]')) {
        return;
      }
      // If clicking anywhere on the card, open the link
      window.open(normalizeUrl(url), '_blank', 'noopener,noreferrer');
    } else {
      // If empty, open edit modal
      onOpenEdit(type);
    }
  };

  const handleEditClick = (e) => {
    e.stopPropagation();
    onOpenEdit(type);
  };

  const handleExternalLinkClick = (e) => {
    e.stopPropagation();
    if (url) {
      window.open(normalizeUrl(url), '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <motion.div
      whileHover={isConnected ? { y: -2 } : {}}
      whileTap={isConnected ? { y: 0 } : {}}
    >
      <Card
        className={`relative border rounded-xl transition-all duration-200 overflow-hidden ${
          isConnected
            ? 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 hover:border-blue-300 hover:shadow-md cursor-pointer group dark:bg-gradient-to-br dark:from-slate-900 dark:to-slate-800 dark:border-white/10 dark:hover:border-white/20'
            : 'bg-gray-50 border-gray-200 hover:border-gray-300 dark:bg-slate-900/50 dark:border-white/5 dark:hover:border-white/10'
        }`}
        onClick={handleCardClick}
      >
        <CardContent className="p-4 space-y-2">
          {/* Header: Label + Edit Icon */}
          <div className="flex items-start justify-between">
            <p className="text-xs uppercase tracking-wider text-gray-500 font-semibold dark:text-gray-400">
              {config.label}
            </p>
            {isConnected && (
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleEditClick}
                className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-white/10"
                title="Edit"
              >
                <Edit2 className="h-4 w-4" />
              </motion.button>
            )}
          </div>

          {/* Content */}
          <div className="flex items-center justify-between gap-2 min-w-0">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <div className="shrink-0">
                <Icon className="h-5 w-5 text-gray-600 dark:text-white/70 group-hover:text-blue-600 dark:group-hover:text-white transition-colors" />
              </div>

              {isConnected ? (
                // Connected State: Show username/display text
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate" title={displayText}>
                    {displayText}
                  </p>
                </div>
              ) : (
                // Empty State: Show placeholder
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-gray-500 dark:text-gray-400">{config.emptyPlaceholder}</p>
                </div>
              )}
            </div>

            {/* External Link Icon - Visible when connected */}
            {isConnected && (
              <motion.button
                data-action="open-link"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleExternalLinkClick}
                className="p-1 rounded-md text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-white/10 shrink-0"
                title="Open"
                disabled={isLoading}
              >
                <ExternalLink className="h-4 w-4" />
              </motion.button>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

/**
 * SocialLinks - Main component
 * Displays all social media links with edit functionality
 */
export default function SocialLinks({ profile, onProfileUpdate }) {
  const [editingType, setEditingType] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleOpenEdit = useCallback((type) => {
    setEditingType(type);
    setError(null);
  }, []);

  const handleCloseEdit = useCallback(() => {
    setEditingType(null);
  }, []);

  const handleSaveUrl = useCallback(
    async (url) => {
      setIsSaving(true);
      setError(null);

      try {
        const fieldMap = {
          github: 'github_url',
          linkedin: 'linkedin_url',
          portfolio: 'portfolio_url',
        };

        const fieldName = fieldMap[editingType];

        // Call API to update
        const response = await updateProfileSocial(fieldName, url);

        // Update local profile state
        if (onProfileUpdate) {
          onProfileUpdate({
            ...profile,
            [fieldName]: url,
          });
        }

        setEditingType(null);
      } catch (err) {
        console.error('Error updating profile:', err);
        setError(err.response?.data?.detail || 'Failed to update profile');
      } finally {
        setIsSaving(false);
      }
    },
    [editingType, profile, onProfileUpdate]
  );

  return (
    <>
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.05 }}
        className="space-y-4"
      >
        {/* Header */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Social & Presence</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Connect your professional profiles to showcase your work
          </p>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Object.entries(SOCIAL_CONFIG).map(([type, config]) => (
            <SocialCard
              key={type}
              type={type}
              url={
                type === 'github'
                  ? profile?.github_url
                  : type === 'linkedin'
                  ? profile?.linkedin_url
                  : profile?.portfolio_url
              }
              isLoading={isSaving && editingType === type}
              onEdit={handleOpenEdit}
              onOpenEdit={handleOpenEdit}
            />
          ))}
        </div>

        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/50 rounded-lg"
          >
            <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
          </motion.div>
        )}
      </motion.section>

      {/* Edit Modal */}
      <SocialEditModal
        isOpen={!!editingType}
        onClose={handleCloseEdit}
        socialType={editingType}
        currentUrl={
          editingType === 'github'
            ? profile?.github_url
            : editingType === 'linkedin'
            ? profile?.linkedin_url
            : profile?.portfolio_url
        }
        onSave={handleSaveUrl}
        isLoading={isSaving}
      />
    </>
  );
}
