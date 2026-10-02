import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      setLoading(true);
      try {
        const response = await fetch('/api/auth/me', {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch user data');
        }

        const data = await response.json();
        setUser(data);
      } catch (err: any) {
        setError(err.message || 'An error occurred');
        // If we can't get the user, we are not authenticated
        navigate('/login', { replace: true });
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [navigate]);

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('Logout failed', err);
    } finally {
      navigate('/login', { replace: true });
    }
  };

  if (loading) {
    return <div className="container">Loading...</div>;
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">{error}</div>
        <button onClick={() => navigate('/login', { replace: true })} className="button-secondary">
          Go to Login
        </button>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container">
        <div className="error">User data not available</div>
        <button onClick={() => navigate('/login', { replace: true })} className="button-secondary">
          Go to Login
        </button>
      </div>
    );
  }

  return (
    <div className="container dashboard">
      <h1>Welcome, {user.name}!</h1>
      <p>
        <strong>Email:</strong> {user.email}
      </p>
      <p>
        <strong>Email Verified:</strong> {user.email_verified ? 'Yes' : 'No'}
      </p>
      <p>
        <strong>Account Created:</strong> {new Date(user.created_at).toLocaleDateString()}
      </p>
      <button onClick={handleLogout} className="logout-btn">
        Logout
      </button>
    </div>
  );
};

export default Dashboard;