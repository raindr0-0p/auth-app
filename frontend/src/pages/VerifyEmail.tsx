import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [verified, setVerified] = useState<boolean | null>(null); // null = checking, true/false = result
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      setError('Invalid or missing token');
      setVerified(false);
      return;
    }

    // Verify the token
    const verifyToken = async () => {
      setLoading(true);
      try {
        const response = await fetch('/api/auth/verify-email', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || 'Verification failed');
        }

        setVerified(true);
        setSuccess('Email verified successfully! Redirecting to login...');
        // Redirect to login after a short delay
        setTimeout(() => {
          navigate('/login');
        }, 1500);
      } catch (err: any) {
        setVerified(false);
        setError(err.message || 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    verifyToken();
  }, [token, navigate]);

  if (verified === false) {
    return (
      <div className="container">
        <h1>Verify Email</h1>
        <div className="error">
          Invalid or expired verification token. Please request a new verification link.
        </div>
        <div className="links">
          <p>
            <a href="/login">Login</a>
          </p>
          <p>
            <a href="/signup">Sign up</a>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>Verify Email</h1>
      {loading && <div className="loading">Verifying your email...</div>}
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      {verified === null && (
        <div className="loading">Checking your verification link...</div>
      )}
    </div>
  );
};

export default VerifyEmail;