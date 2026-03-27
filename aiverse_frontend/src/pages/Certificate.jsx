import { useState, useEffect, useRef } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Award,
  Download,
  Share2,
  Copy,
  Check,
  ArrowLeft,
  Calendar,
  User,
  BookOpen,
  QrCode,
  ExternalLink,
  Shield,
  Loader2,
} from 'lucide-react';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import api from '../api/axios';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';

/**
 * Certificate Page
 * 
 * Two modes:
 * 1. /learn/courses/:slug/certificate - User's own certificate (authenticated)
 * 2. /certificates/verify/:certificateId - Public verification page
 * 
 * Features:
 * - Certificate display with QR code
 * - PDF download
 * - Share functionality
 * - Public verification
 */
export default function Certificate() {
  const { slug, certificateId } = useParams();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, user } = useAuth();

  const [certificate, setCertificate] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Determine if this is verification mode
  const isVerifyMode = !!certificateId;

  useEffect(() => {
    fetchCertificate();
  }, [slug, certificateId]);

  const fetchCertificate = async () => {
    try {
      setIsLoading(true);
      setError(null);

      let response;
      if (isVerifyMode) {
        // Public verification endpoint
        response = await api.get(`/api/learn/certificates/verify/${certificateId}/`);
      } else if (slug) {
        // User's certificate for a course
        response = await api.get(`/api/learn/courses/${slug}/certificate/`);
      } else {
        throw new Error('Invalid certificate request');
      }

      setCertificate(response.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setError(
          isVerifyMode
            ? 'Certificate not found or invalid'
            : 'You have not earned a certificate for this course yet'
        );
      } else if (err.response?.status === 403) {
        setError('You must complete the course to earn a certificate');
      } else {
        setError(
          err.response?.data?.message ||
            err.response?.data?.error ||
            'Failed to load certificate'
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!certificate?.pdf_url) {
      // Generate PDF if not available
      try {
        setIsDownloading(true);
        const response = await api.post(
          `/api/learn/certificates/${certificate.id}/generate-pdf/`,
          {},
          { responseType: 'blob' }
        );

        // Create download link
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `certificate-${certificate.certificate_id}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        toast.success('Certificate downloaded!');
      } catch (err) {
        toast.error('Failed to download certificate');
      } finally {
        setIsDownloading(false);
      }
      return;
    }

    // Direct download if PDF URL is available
    window.open(certificate.pdf_url, '_blank');
  };

  const handleCopyLink = () => {
    const verifyUrl = `${window.location.origin}/certificates/verify/${certificate.certificate_id}`;
    navigator.clipboard.writeText(verifyUrl);
    setCopied(true);
    toast.success('Verification link copied!');
    setTimeout(() => setCopied(false), 3000);
  };

  const handleShare = async () => {
    const verifyUrl = `${window.location.origin}/certificates/verify/${certificate.certificate_id}`;
    const shareData = {
      title: `Certificate - ${certificate.course?.title || 'Course Completion'}`,
      text: `I completed "${certificate.course?.title}" on AIverse!`,
      url: verifyUrl,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        if (err.name !== 'AbortError') {
          handleCopyLink();
        }
      }
    } else {
      handleCopyLink();
    }
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <Layout>
        <div className="min-h-[60vh] flex items-center justify-center">
          <LoadingSpinner text="Loading certificate..." />
        </div>
      </Layout>
    );
  }

  // Error state
  if (error || !certificate) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-12">
          <ErrorState message={error || 'Certificate not found'} onRetry={fetchCertificate} />
          {!isVerifyMode && slug && (
            <div className="text-center mt-6">
              <Link
                to={`/learn/courses/${slug}`}
                className="text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                <ArrowLeft className="w-4 h-4 inline mr-2" />
                Back to Course
              </Link>
            </div>
          )}
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="min-h-[80vh] py-12">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Back link */}
          {!isVerifyMode && (
            <Link
              to={`/learn/courses/${slug}`}
              className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Course
            </Link>
          )}

          {/* Verification Badge (for verify mode) */}
          {isVerifyMode && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-8"
            >
              <Badge
                variant="secondary"
                className="bg-emerald-500/10 text-emerald-600 text-sm px-4 py-2"
              >
                <Shield className="w-4 h-4 mr-2" />
                Verified Certificate
              </Badge>
            </motion.div>
          )}

          {/* Certificate Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-card border border-border rounded-2xl overflow-hidden shadow-xl"
          >
            {/* Certificate Header */}
            <div className="bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-8 border-b border-border">
              <div className="flex items-center justify-center gap-3 mb-4">
                <Award className="w-10 h-10 text-primary" />
                <h1 className="text-2xl font-bold text-foreground">
                  Certificate of Completion
                </h1>
              </div>
              <p className="text-center text-muted-foreground">
                AIverse ML Engineering Academy
              </p>
            </div>

            {/* Certificate Body */}
            <div className="p-8 lg:p-12">
              <div className="text-center mb-8">
                <p className="text-muted-foreground mb-2">This certifies that</p>
                <h2 className="text-3xl font-bold text-foreground mb-2">
                  {certificate.user?.full_name ||
                    certificate.user?.username ||
                    certificate.recipient_name ||
                    'Student'}
                </h2>
                <p className="text-muted-foreground">
                  has successfully completed the course
                </p>
              </div>

              {/* Course Title */}
              <div className="text-center mb-8">
                <h3 className="text-2xl font-semibold text-primary">
                  {certificate.course?.title || certificate.course_title}
                </h3>
                {certificate.course?.description && (
                  <p className="text-sm text-muted-foreground mt-2 max-w-lg mx-auto">
                    {certificate.course.description}
                  </p>
                )}
              </div>

              {/* Details Grid */}
              <div className="grid sm:grid-cols-3 gap-6 mb-8">
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <Calendar className="w-5 h-5 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-xs text-muted-foreground mb-1">
                    Date Issued
                  </p>
                  <p className="font-semibold">
                    {formatDate(certificate.issued_at || certificate.created_at)}
                  </p>
                </div>

                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <User className="w-5 h-5 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-xs text-muted-foreground mb-1">
                    Recipient
                  </p>
                  <p className="font-semibold truncate">
                    {certificate.user?.email || 'Verified Student'}
                  </p>
                </div>

                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <BookOpen className="w-5 h-5 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-xs text-muted-foreground mb-1">
                    Certificate ID
                  </p>
                  <p className="font-mono text-sm font-semibold">
                    {certificate.certificate_id?.slice(0, 8) ||
                      certificate.id?.toString().slice(0, 8)}
                  </p>
                </div>
              </div>

              {/* QR Code */}
              {certificate.qr_code_url && (
                <div className="flex justify-center mb-8">
                  <div className="p-4 bg-white rounded-lg">
                    <img
                      src={certificate.qr_code_url}
                      alt="Verification QR Code"
                      className="w-32 h-32"
                    />
                  </div>
                </div>
              )}

              {/* Verification URL */}
              <div className="text-center">
                <p className="text-xs text-muted-foreground mb-2">
                  Verify this certificate at:
                </p>
                <code className="text-xs bg-muted px-3 py-1.5 rounded-lg">
                  {window.location.origin}/certificates/verify/
                  {certificate.certificate_id || certificate.id}
                </code>
              </div>
            </div>

            {/* Certificate Footer - Actions */}
            <div className="p-6 bg-muted/30 border-t border-border">
              <div className="flex flex-wrap justify-center gap-3">
                <Button
                  onClick={handleDownload}
                  disabled={isDownloading}
                  className="bg-primary hover:bg-primary/90"
                >
                  {isDownloading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4 mr-2" />
                  )}
                  Download PDF
                </Button>

                <Button variant="outline" onClick={handleShare}>
                  <Share2 className="w-4 h-4 mr-2" />
                  Share
                </Button>

                <Button variant="outline" onClick={handleCopyLink}>
                  {copied ? (
                    <Check className="w-4 h-4 mr-2" />
                  ) : (
                    <Copy className="w-4 h-4 mr-2" />
                  )}
                  {copied ? 'Copied!' : 'Copy Link'}
                </Button>
              </div>
            </div>
          </motion.div>

          {/* Additional Info */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-8 text-center"
          >
            <p className="text-sm text-muted-foreground">
              This certificate was issued by AIverse and can be independently
              verified using the QR code or verification URL above.
            </p>

            {isVerifyMode && (
              <div className="mt-6">
                <Link to="/learn">
                  <Button variant="outline">
                    <BookOpen className="w-4 h-4 mr-2" />
                    Browse Courses
                  </Button>
                </Link>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </Layout>
  );
}
