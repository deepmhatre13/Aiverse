import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Eye, EyeOff, Mail, Lock, Loader2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const googleButtonRef = useRef(null);
  const gsiInitializedRef = useRef(false);
  
  const { login, googleLogin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // ===== GOOGLE SIGN-IN INITIALIZATION =====
  useEffect(() => {
    let mounted = true;

    // Check Client ID
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      console.error('❌ VITE_GOOGLE_CLIENT_ID not set in .env');
      setError('Google Sign-In not configured');
      return;
    }

    const setupGoogleButton = () => {
      if (!mounted || !window.google?.accounts?.id || !googleButtonRef.current) {
        return;
      }

      try {
        // StrictMode can run effects twice in development; initialize once.
        if (!gsiInitializedRef.current) {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: handleGoogleCallback,
            auto_select: false,
            itp_support: true,
          });
          gsiInitializedRef.current = true;
        }

        googleButtonRef.current.innerHTML = '';
        window.google.accounts.id.renderButton(googleButtonRef.current, {
          type: 'standard',
          size: 'large',
          text: 'continue_with',
          shape: 'rectangular',
          logo_alignment: 'center',
        });

        console.log('✅ Google Sign-In button rendered');
      } catch (error) {
        console.error('❌ Error initializing Google Sign-In:', error);
        setError('Failed to initialize Google Sign-In');
      }
    };

    // Reuse an existing GSI script if it has already been loaded.
    const existingScript = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
    let script = existingScript;

    if (!script) {
      script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }

    script.onload = () => {
      if (!mounted) return;
      console.log('✅ Google Identity Services script loaded');
      setupGoogleButton();
    };

    if (window.google?.accounts?.id) {
      setupGoogleButton();
    }

    script.onerror = () => {
      console.error('❌ Failed to load Google Identity Services');
      setError('Failed to load Google Sign-In');
    };

    // Cleanup
    return () => {
      mounted = false;
    };
  }, []);

  // ===== HANDLE GOOGLE CALLBACK =====
  const handleGoogleCallback = async (response) => {
    console.log('🔄 Google callback received', response);

    // ✅ FIX: Strict validation of credential format
    if (!response) {
      console.error('❌ No response object from Google');
      toast.error('Google Sign-In failed: No response');
      return;
    }

    if (typeof response.credential !== 'string') {
      console.error('❌ Credential is not a string', typeof response.credential, response.credential);
      toast.error('Failed to get credential from Google');
      return;
    }

    if (response.credential.length < 100) {
      console.error('❌ Credential too short (likely invalid)', response.credential.length);
      toast.error('Invalid credential from Google');
      return;
    }

    const idToken = response.credential;
    console.log(`✅ Credential received (${idToken.length} chars): ${idToken.substring(0, 50)}...`);
    
    setIsLoading(true);
    setError('');

    try {
      // Use the googleLogin function from AuthContext
      // This handles token storage AND auth state updates immediately
      await googleLogin(idToken);
      
      console.log('✅ Authentication successful');
      toast.success('Welcome!');
      
      // Navigate to dashboard immediately
      // AuthContext has already updated isAuthenticated=true
      // so ProtectedRoute will allow access
      navigate('/dashboard', { replace: true });
    } catch (err) {
      console.error('❌ Google login error:', err);
      const errorMsg = err.response?.data?.error || 
                       err.response?.data?.detail || 
                       err.message || 
                       'Authentication failed';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      toast.success('Welcome back!');
      navigate(from, { replace: true });
    } catch (err) {
      let errorMessage = 'Invalid credentials';
      
      if (err.response?.data) {
        const errorData = err.response.data;
        if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.non_field_errors) {
          errorMessage = Array.isArray(errorData.non_field_errors) 
            ? errorData.non_field_errors[0] 
            : errorData.non_field_errors;
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        }
      }
      
      console.error('Login error:', err.response?.data || err);
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 mb-8">
            <div className="w-10 h-10 rounded-lg gradient-wine flex items-center justify-center">
              <span className="text-primary-foreground font-serif font-bold text-xl">A</span>
            </div>
            <span className="font-serif text-2xl font-semibold">Aiverse</span>
          </Link>

          <div className="mb-8">
            <h1 className="heading-secondary text-foreground mb-2">Welcome back</h1>
            <p className="text-muted-foreground">
              Sign in to continue your learning journey
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-destructive mt-0.5 shrink-0" />
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          {/* Google Sign In - Official Google Button */}
          <div className="mb-6">
            <div ref={googleButtonRef} id="google-signin-button" />
          </div>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or continue with email</span>
            </div>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-12 pl-10"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <a href="#" className="text-sm text-primary hover:underline">
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-12 pl-10 pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <Button type="submit" className="w-full h-12 text-base btn-wine" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </Button>
          </form>

          <p className="mt-8 text-center text-muted-foreground">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary font-medium hover:underline">
              Create account
            </Link>
          </p>
        </div>
      </div>

      {/* Right Side - Visual */}
      <div className="hidden lg:flex flex-1 gradient-wine items-center justify-center p-12">
        <div className="max-w-lg text-primary-foreground text-center">
          <h2 className="heading-secondary mb-6">
            Think Deeper, Learn Better
          </h2>
          <p className="text-lg opacity-90 mb-8">
            Join our community of ML engineers who prioritize understanding over memorization.
          </p>
          <div className="grid grid-cols-3 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold mb-1">10K+</div>
              <div className="text-sm opacity-80">Active Learners</div>
            </div>
            <div>
              <div className="text-3xl font-bold mb-1">500+</div>
              <div className="text-sm opacity-80">ML Problems</div>
            </div>
            <div>
              <div className="text-3xl font-bold mb-1">50+</div>
              <div className="text-sm opacity-80">Courses</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}