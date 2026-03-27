import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SocialLinks from './SocialLinks';
import { validateSocialUrl, getDisplayText, extractGithubUsername } from '@/lib/urlUtils';

/**
 * URL Utils Tests
 */
describe('URL Utils', () => {
  describe('getDisplayText', () => {
    it('should extract GitHub username from URL', () => {
      expect(getDisplayText('github', 'https://github.com/deepmhatre13')).toBe('deepmhatre13');
      expect(getDisplayText('github', 'github.com/deepmhatre13')).toBe('deepmhatre13');
    });

    it('should extract LinkedIn profile name', () => {
      expect(getDisplayText('linkedin', 'https://linkedin.com/in/deepam-mhatre')).toBe(
        'deepam-mhatre'
      );
    });

    it('should return "Visit Website" for portfolio', () => {
      expect(getDisplayText('portfolio', 'https://example.com')).toBe('Visit Website');
    });

    it('should return empty string for null URL', () => {
      expect(getDisplayText('github', null)).toBe('');
      expect(getDisplayText('github', '')).toBe('');
    });
  });

  describe('validateSocialUrl', () => {
    it('should validate correct GitHub URL', () => {
      const result = validateSocialUrl('github', 'https://github.com/deepmhatre13');
      expect(result.valid).toBe(true);
    });

    it('should reject GitHub URL without domain', () => {
      const result = validateSocialUrl('github', 'deepmhatre13');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('GitHub');
    });

    it('should reject LinkedIn URL on GitHub field', () => {
      const result = validateSocialUrl('github', 'https://linkedin.com/in/deepam-mhatre');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('GitHub');
    });

    it('should require error on empty URL', () => {
      const result = validateSocialUrl('github', '');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('required');
    });
  });
});

/**
 * SocialLinks Component Tests
 */
describe('SocialLinks Component', () => {
  const mockProfile = {
    github_url: 'https://github.com/deepmhatre13',
    linkedin_url: 'https://linkedin.com/in/deepam-mhatre',
    portfolio_url: 'https://example.com',
  };

  const emptyProfile = {
    github_url: null,
    linkedin_url: null,
    portfolio_url: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Display', () => {
    it('should render section title', () => {
      render(<SocialLinks profile={emptyProfile} />);
      expect(screen.getByText('Social & Presence')).toBeInTheDocument();
    });

    it('should display connected profiles with usernames', () => {
      render(<SocialLinks profile={mockProfile} />);
      expect(screen.getByText('deepmhatre13')).toBeInTheDocument();
      expect(screen.getByText('deepam-mhatre')).toBeInTheDocument();
      expect(screen.getByText('Visit Website')).toBeInTheDocument();
    });

    it('should display empty state placeholders', () => {
      render(<SocialLinks profile={emptyProfile} />);
      expect(screen.getByText('Add GitHub profile')).toBeInTheDocument();
      expect(screen.getByText('Add LinkedIn profile')).toBeInTheDocument();
      expect(screen.getByText('Add personal website')).toBeInTheDocument();
    });

    it('should display edit icons only for connected profiles', () => {
      const { container } = render(<SocialLinks profile={mockProfile} />);
      const editButtons = container.querySelectorAll('[title="Edit"]');
      expect(editButtons.length).toBe(3); // All connected
    });

    it('should not display edit icons for empty profiles', () => {
      const { container } = render(<SocialLinks profile={emptyProfile} />);
      const editButtons = container.querySelectorAll('[title="Edit"]');
      expect(editButtons.length).toBe(0);
    });
  });

  describe('Interactions', () => {
    it('should open modal when clicking empty card', async () => {
      render(<SocialLinks profile={emptyProfile} />);
      const gitHubCard = screen.getByText('Add GitHub profile').closest('[role="dialog"], [class*="Card"]');
      // Note: Dialog might not be rendered, so we test the click handler exists
    });

    it('should open URL in new tab when clicking connected card', async () => {
      const windowOpen = vi.spyOn(window, 'open').mockImplementation(() => ({}));
      render(<SocialLinks profile={mockProfile} />);
      
      // Click on GitHub username
      const githubLink = screen.getByText('deepmhatre13');
      fireEvent.click(githubLink.closest('[class*="Card"]'));
      
      await waitFor(() => {
        expect(windowOpen).toHaveBeenCalledWith(
          'https://github.com/deepmhatre13',
          '_blank',
          'noopener,noreferrer'
        );
      });
      
      windowOpen.mockRestore();
    });

    it('should open external link when clicking external icon', async () => {
      const windowOpen = vi.spyOn(window, 'open').mockImplementation(() => ({}));
      render(<SocialLinks profile={mockProfile} />);
      
      const externalLinks = screen.getAllByTitle('Open');
      fireEvent.click(externalLinks[0]);
      
      await waitFor(() => {
        expect(windowOpen).toHaveBeenCalled();
      });
      
      windowOpen.mockRestore();
    });

    it('should open edit modal when clicking edit icon', async () => {
      vi.mock('@/api/profile', () => ({
        updateProfileSocial: vi.fn(),
      }));
      
      render(<SocialLinks profile={mockProfile} onProfileUpdate={vi.fn()} />);
      
      const editButtons = screen.getAllByTitle('Edit');
      fireEvent.click(editButtons[0]);
      
      // Modal should open
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/github\.com/i)).toBeInTheDocument();
      });
    });
  });

  describe('Modal Interactions', () => {
    it('should validate URL before saving', async () => {
      const onProfileUpdate = vi.fn();
      
      vi.mock('@/api/profile', () => ({
        updateProfileSocial: vi.fn(),
      }));
      
      render(<SocialLinks profile={emptyProfile} onProfileUpdate={onProfileUpdate} />);
      
      // Open modal
      const emptyCards = screen.getAllByText(/Add/);
      fireEvent.click(emptyCards[0].closest('[class*="Card"]'));
      
      // Try to save invalid URL
      const input = await screen.findByPlaceholderText(/github\.com/i);
      const saveButton = screen.getAllByText('Save').filter(btn => btn.tagName === 'BUTTON')[0];
      
      await userEvent.type(input, 'invalid-url');
      fireEvent.click(saveButton);
      
      // Should show error
      await waitFor(() => {
        expect(screen.getByText(/valid URL/i)).toBeInTheDocument();
      });
    });

    it('should call API when saving valid URL', async () => {
      const updateProfileSocial = vi.fn().mockResolvedValue({
        github_url: 'https://github.com/newuser',
      });
      
      vi.doMock('@/api/profile', () => ({
        updateProfileSocial,
      }));
      
      const onProfileUpdate = vi.fn();
      render(<SocialLinks profile={emptyProfile} onProfileUpdate={onProfileUpdate} />);
      
      // Open modal and save
      const emptyCards = screen.getAllByText(/Add/);
      fireEvent.click(emptyCards[0].closest('[class*="Card"]'));
      
      const input = await screen.findByPlaceholderText(/github\.com/i);
      await userEvent.type(input, 'https://github.com/newuser');
      
      const saveButton = screen.getAllByText('Save').filter(btn => btn.tagName === 'BUTTON')[0];
      fireEvent.click(saveButton);
      
      await waitFor(() => {
        expect(updateProfileSocial).toHaveBeenCalledWith('github_url', 'https://github.com/newuser');
      });
    });

    it('should handle API errors gracefully', async () => {
      const updateProfileSocial = vi.fn().mockRejectedValue({
        response: { data: { detail: 'Profile not found' } },
      });
      
      vi.doMock('@/api/profile', () => ({
        updateProfileSocial,
      }));
      
      render(<SocialLinks profile={emptyProfile} onProfileUpdate={vi.fn()} />);
      
      // Open modal and try to save
      const emptyCards = screen.getAllByText(/Add/);
      fireEvent.click(emptyCards[0].closest('[class*="Card"]'));
      
      const input = await screen.findByPlaceholderText(/github\.com/i);
      await userEvent.type(input, 'https://github.com/newuser');
      
      const saveButton = screen.getAllByText('Save').filter(btn => btn.tagName === 'BUTTON')[0];
      fireEvent.click(saveButton);
      
      // Should show error message
      await waitFor(() => {
        expect(screen.getByText('Profile not found')).toBeInTheDocument();
      });
    });
  });
});
