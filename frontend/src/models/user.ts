import type { UserInfomation } from '@/interfaces/user';
import { requestUserInfo, requestValidateToken } from '@/request/userAuthorization';
import { useEffect, useState } from 'react';
import { history } from 'umi';
import { message } from 'antd';

const useUser = () => {
  const [userInfo, setUserInfo] = useState<UserInfomation | null>(null);

  const isGuestMode = () => localStorage.getItem('isGuest') === 'true';

  const handleTokenExpiration = () => {
    const hadToken = localStorage.getItem('token') !== null;
    localStorage.removeItem('token');
    setUserInfo(null);

    const currentPath = window.location.pathname;
    if (!currentPath.includes('/login/')) {
      if (hadToken) {
        message.error('Your session has expired. Please log in again.');
      }
      history.push('/login/byPassword');
    }
  };

  const validateToken = async () => {
    try {
      const response = await requestValidateToken();
      if (!response.data) {
        handleTokenExpiration();
        return false;
      }
      return true;
    } catch (error) {
      console.error('Error validating token:', error);
      handleTokenExpiration();
      return false;
    }
  };

  const getUserInfo = async () => {
    try {
      if (isGuestMode()) {
        setUserInfo(null);
        return;
      }

      const { data: userInfo } = await requestUserInfo();
      setUserInfo(userInfo);
    } catch (error) {
      console.error('Error fetching user info:', error);
      setUserInfo(null);
    }
  };

  const immediateRefresh = async () => {
    if (!isGuestMode()) {
      const isValid = await validateToken();
      if (!isValid) return;
    }

    try {
      await getUserInfo();
    } catch (error) {
      console.error('Error during immediate refresh:', error);
    }
  };

  const startAutoRefresh = () => {
    immediateRefresh();
    const interval = setInterval(immediateRefresh, 1000 * 60);
    return () => clearInterval(interval);
  };

  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'isGuest') {
        immediateRefresh();
      }
    };

    const handleUserStateChange = () => {
      immediateRefresh();
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('userStateChange', handleUserStateChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('userStateChange', handleUserStateChange);
    };
  }, []);

  useEffect(startAutoRefresh, []);

  return {
    userInfo,
    setUserInfo,
    immediateRefresh,
    isGuest: isGuestMode,
    validateToken,
  };
};

export default useUser;
