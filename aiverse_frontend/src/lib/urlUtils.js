/**
 * URL Parsing & Validation Utilities
 * Handles extraction of usernames and display text from social URLs
 */

/**
 * Normalize URL - ensure it has protocol
 */
export function normalizeUrl(value) {
  if (!value) return '';
  value = value.trim();
  if (!value) return '';
  return value.startsWith('http://') || value.startsWith('https://') ? value : `https://${value}`;
}

/**
 * Validate URL format
 */
export function isValidUrl(value) {
  try {
    const url = new URL(normalizeUrl(value));
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

/**
 * Extract username from GitHub URL
 * https://github.com/deepmhatre13 -> deepmhatre13
 */
export function extractGithubUsername(url) {
  if (!url) return '';
  try {
    const normalized = normalizeUrl(url);
    const urlObj = new URL(normalized);
    const path = urlObj.pathname.replace(/^\/+|\/+$/g, '');
    return path.split('/')[0] || '';
  } catch {
    return '';
  }
}

/**
 * Extract name from LinkedIn URL
 * https://linkedin.com/in/deepam-mhatre -> deepam-mhatre
 */
export function extractLinkedinName(url) {
  if (!url) return '';
  try {
    const normalized = normalizeUrl(url);
    const urlObj = new URL(normalized);
    const path = urlObj.pathname.replace(/^\/+|\/+$/g, '');
    // Handle both /in/name and /company/name formats
    const segments = path.split('/').filter(Boolean);
    return segments[segments.length - 1] || '';
  } catch {
    return '';
  }
}

/**
 * Get display text based on platform and URL
 */
export function getDisplayText(type, url) {
  if (!url) return '';

  switch (type) {
    case 'github':
      return extractGithubUsername(url);
    case 'linkedin':
      return extractLinkedinName(url);
    case 'portfolio':
      return 'Visit Website';
    default:
      return '';
  }
}

/**
 * Validate URL against platform requirements
 */
export function validateSocialUrl(type, url) {
  if (!url) return { valid: false, error: 'URL is required' };

  if (!isValidUrl(url)) {
    return { valid: false, error: 'Please enter a valid URL' };
  }

  try {
    const normalized = normalizeUrl(url);
    const urlObj = new URL(normalized);
    const hostname = urlObj.hostname.toLowerCase();

    switch (type) {
      case 'github':
        if (!hostname.includes('github.com')) {
          return { valid: false, error: 'Please enter a valid GitHub URL' };
        }
        const ghUsername = extractGithubUsername(url);
        if (!ghUsername) {
          return { valid: false, error: 'GitHub URL must include a username' };
        }
        return { valid: true };

      case 'linkedin':
        if (!hostname.includes('linkedin.com')) {
          return { valid: false, error: 'Please enter a valid LinkedIn URL' };
        }
        const liName = extractLinkedinName(url);
        if (!liName) {
          return { valid: false, error: 'LinkedIn URL must include a profile name' };
        }
        return { valid: true };

      case 'portfolio':
        // Any valid URL is acceptable for portfolio
        return { valid: true };

      default:
        return { valid: false, error: 'Unknown social platform' };
    }
  } catch {
    return { valid: false, error: 'Invalid URL format' };
  }
}

/**
 * Get placeholder URL for each platform
 */
export function getPlaceholder(type) {
  switch (type) {
    case 'github':
      return 'https://github.com/username';
    case 'linkedin':
      return 'https://linkedin.com/in/your-name';
    case 'portfolio':
      return 'https://yourwebsite.com';
    default:
      return 'https://example.com';
  }
}
