import api from './axios';

/**
 * Fetch user profile
 */
export async function fetchProfile() {
  try {
    const response = await api.get('/api/users/profile/');
    return response.data;
  } catch (error) {
    console.error('Error fetching profile:', error);
    throw error;
  }
}

/**
 * Update a single social media URL
 * @param {string} fieldName - 'github_url' | 'linkedin_url' | 'portfolio_url'
 * @param {string|null} url - The URL to set, or null to clear
 */
export async function updateProfileSocial(fieldName, url) {
  try {
    const response = await api.put('/api/users/profile/', {
      [fieldName]: url,
    });
    return response.data;
  } catch (error) {
    console.error(`Error updating ${fieldName}:`, error);
    throw error;
  }
}

/**
 * Update full profile
 * @param {object} data - Profile data to update
 */
export async function updateProfile(data) {
  try {
    const response = await api.put('/api/users/profile/', data);
    return response.data;
  } catch (error) {
    console.error('Error updating profile:', error);
    throw error;
  }
}
