import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { Toaster } from './components/ui/sonner';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Problems from './pages/Problems';
import ProblemDetail from './pages/ProblemDetail';
import Submissions from './pages/Submissions';
import Learn from './pages/Learn';
import CourseDetail from './pages/CourseDetail';
import Lesson from './pages/Lesson';
import FinalQuiz from './pages/FinalQuiz';
import Certificate from './pages/Certificate';
import Mentor from './pages/Mentor';
import Playground from './pages/Playground';
import LivePerformanceCenter from './pages/LivePerformanceCenter';
import Leaderboard from './pages/Leaderboard';
import Profile from './pages/Profile';
import Discussions from './pages/Discussions';
import DiscussionDetail from './pages/DiscussionDetail';
import NotFound from './pages/NotFound';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true,
            }}
          >
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/problems" element={<Problems />} />
              <Route path="/problems/:slug" element={<ProblemDetail />} />
              <Route path="/submissions" element={<ProtectedRoute><Submissions /></ProtectedRoute>} />
              <Route path="/learn" element={<Learn />} />
              <Route path="/learn/courses/:slug" element={<CourseDetail />} />
              <Route path="/learn/courses/:slug/lessons/:lessonSlug" element={<ProtectedRoute><Lesson /></ProtectedRoute>} />
              <Route path="/learn/courses/:slug/final-quiz" element={<ProtectedRoute><FinalQuiz /></ProtectedRoute>} />
              <Route path="/learn/courses/:slug/certificate" element={<ProtectedRoute><Certificate /></ProtectedRoute>} />
              <Route path="/certificates/verify/:certificateId" element={<Certificate />} />
              <Route path="/mentor" element={<ProtectedRoute><Mentor /></ProtectedRoute>} />
              <Route path="/playground" element={<ProtectedRoute><Playground /></ProtectedRoute>} />
              <Route path="/live" element={<ProtectedRoute><LivePerformanceCenter /></ProtectedRoute>} />
              {/* Redirects from old routes */}
              <Route path="/dashboard" element={<Navigate to="/live" replace />} />
              <Route path="/timeline" element={<Navigate to="/live" replace />} />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
              <Route path="/discussions" element={<Discussions />} />
              <Route path="/discussions/:id" element={<DiscussionDetail />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
            <Toaster position="top-right" />
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
