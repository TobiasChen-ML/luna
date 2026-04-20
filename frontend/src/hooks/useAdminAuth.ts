import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/services/api';

interface UseAdminAuthResult {
  isAdmin: boolean;
  loading: boolean;
  user: any;
}

export function useAdminAuth(): UseAdminAuthResult {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    checkAdminAuth();
  }, []);

  const checkAdminAuth = async () => {
    try {
      const response = await api.get('/auth/me');
      if (response.data?.is_admin) {
        setIsAdmin(true);
        setUser(response.data);
      } else {
        navigate('/admin/login');
      }
    } catch (error) {
      navigate('/admin/login');
    } finally {
      setLoading(false);
    }
  };

  return { isAdmin, loading, user };
}
