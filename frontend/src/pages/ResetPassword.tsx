import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null); // null = checking, true/false = result

  useEffect(() => {
    if (!token) {
      setError('Invalid or missing token');
      setTokenValid(false);
      return;
    }

    // We can optionally validate the token by hitting an endpoint, but for simplicity,
    // we'll just check the format and let the backend validate it on submit.
    // However, to give early feedback, we can do a light check (e.g., length).
    // But note: we don't want to leak information about the token via error messages.
    // So we'll just set a state to show we're checking and then let the submit handle validation.
    setTokenValid(true); // Assume valid for now, let backend decide
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ token, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Reset failed');
      }

      // Success
      setSuccess('Password has been reset successfully. Redirecting to login...');
      // Redirect to login after a short delay
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (tokenValid === false) {
    return (
      <div className="container">
        <h1>Reset Password</h1>
        <div className="error">
          Invalid or expired token. Please request a new password reset link.
        </div>
        <div className="links">
          <p>
            <a href="/forgot-password">Forgot password?</a>
          </p>
          <p>
            <a href="/login">Login</a>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>Reset Password</h1>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="password">New Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password:</label>
          <input
            type="password"
            id="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
            disabled={loading}
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Resetting password...' : 'Reset Password'}
        </button>
      </form>
      <div className="links">
        <p>
          <a href="/forgot-password">Forgot password?</a>
        </p>
        <p>
          <a href="/login">Login</a>
        </p>
      </div>
    </div>
  );
};

export default ResetPassword;