import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/axios';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const fetchUser = useCallback(async () => {
    try {
      const accessToken = localStorage.getItem('access');
      if (!accessToken) {
        setIsLoading(false);
        return;
      }

      const response = await api.get('/api/users/me/');
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      if (error?.response?.status !== 401) {
        console.error('Failed to fetch user:', error);
      }
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email, password) => {
    try {
      const response = await api.post('/api/users/login/', { email, password });
      
      // Backend returns: { user, tokens: { access, refresh } }
      const { tokens, user: userData } = response.data || {};
      
      if (tokens) {
        localStorage.setItem('access', tokens.access);
        localStorage.setItem('refresh', tokens.refresh);
      } else if (response.data) {
        // Fallback for different response structure
        localStorage.setItem('access', response.data.access);
        localStorage.setItem('refresh', response.data.refresh);
      }
      
      // Fetch full user data
      if (userData) {
        setUser(userData);
        setIsAuthenticated(true);
        setIsLoading(false);  // CRITICAL: Must set isLoading to false so ProtectedRoute allows navigation
      } else {
        // Fetch user data from /api/users/me/
        await fetchUser();
      }
      
      return response.data;
    } catch (error) {
      // Re-throw error so calling code can handle it
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      // Backend expects: { email, password, full_name }
      // Remove confirm_password if present
      const { confirmPassword, name, ...payload } = userData;
      
      // Map 'name' to 'full_name' if needed
      const registerPayload = {
        email: payload.email,
        password: payload.password,
        full_name: payload.full_name || name || '',
      };
      
      const response = await api.post('/api/users/register/', registerPayload);
      
      // Backend returns: { user, tokens: { access, refresh } }
      const { tokens, user: newUser } = response.data || {};
      
      if (tokens) {
        localStorage.setItem('access', tokens.access);
        localStorage.setItem('refresh', tokens.refresh);
      } else if (response.data) {
        // Fallback for different response structure
        localStorage.setItem('access', response.data.access);
        localStorage.setItem('refresh', response.data.refresh);
      }
      
      // Fetch full user data
      if (newUser) {
        setUser(newUser);
        setIsAuthenticated(true);
        setIsLoading(false);  // CRITICAL: Must set isLoading to false so ProtectedRoute allows navigation
      } else {
        // Fetch user data from /api/users/me/
        await fetchUser();
      }
      
      return response.data;
    } catch (error) {
      // Re-throw error so calling code can handle it
      throw error;
    }
  };

  const googleLogin = async (idToken) => {
    try {
      // Backend endpoint: /api/auth/google/ with field name 'credential'
      const response = await api.post('/api/auth/google/', { credential: idToken });
      console.log('Response:', response.data);
      
      // Backend returns: { access, refresh, user }
      const { access, refresh, user: userData } = response.data || {};
      
      if (access && refresh) {
        localStorage.setItem('access', access);
        localStorage.setItem('refresh', refresh);
      } else {
        throw new Error('Invalid response: missing tokens');
      }
      
      // Set authenticated state IMMEDIATELY (synchronous)
      // This allows ProtectedRoute to pass through immediately after navigation
      setUser(userData || null);
      setIsAuthenticated(true);
      setIsLoading(false);
      
      return response.data;
    } catch (error) {
      // Clear any partial state on error
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    setUser(null);
    setIsAuthenticated(false);
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    googleLogin,
    logout,
    fetchUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}