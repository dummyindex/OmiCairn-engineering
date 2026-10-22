import { requestUserInfo } from '@/request/userAuthorization';
import { AuthService } from '@/services/auth/AuthService';
import { cutString } from '@/util/stringHelpers';
import { message } from 'antd';
import type { RequestConfig } from 'umi';
import { history } from 'umi';

interface InitialState {
  userInfo?: any;
}

const initialState: InitialState = {};

export async function getInitialState(): Promise<InitialState> {
  if (localStorage.getItem('token')) {
    try {
      const [userInfoResponse] = await Promise.all([requestUserInfo()]);
      if (userInfoResponse?.data) {
        return {
          userInfo: userInfoResponse.data,
        };
      }
    } catch (error) {
      const currentPath = window.location.pathname;
      if (!currentPath.includes('/login/')) {
        AuthService.getInstance().handleTokenExpiration();
      }
    }
  }
  return initialState;
}

enum ErrorShowType {
  SILENT = 0,
  WARN_MESSAGE = 1,
  ERROR_MESSAGE = 2,
  NOTIFICATION = 3,
  REDIRECT = 9,
}

interface ResponseStructure {
  success: boolean;
  data: any;
  errorCode?: number;
  errorMessage?: string;
  showType?: ErrorShowType;
  response?: any;
}

export const request: RequestConfig = {
  timeout: 1000 * 60 * 5,
  errorConfig: {
    errorThrower: (res: ResponseStructure) => {
      const { success, data, errorCode, errorMessage, showType } = res;
      if (!success) {
        const error: any = new Error(errorMessage);
        error.name = 'BizError';
        error.info = { errorCode, errorMessage, showType, data };
        throw error;
      }
    },
    errorHandler: (error: any) => {
      if (error.response?.data?.code) {
        // Axios error
        // The request was sent and the server responded, but the status code is outside the 2xx range
        // message.error(`${error.response.data.message}`);
        switch (error.response.data.code) {
          case 200: {
            return;
          }
          case 400: {
            message.error(`${cutString(error.response.data.message, 60)}`);
            return;
          }
          case 401: {
            const errorMessage = error.response.data.message;
            if (errorMessage?.includes('no authority for this analysis')) {
              return;
            } else if (errorMessage?.includes('token')) {
              message.error('Your session has expired. Please log in again.');
            } else {
              message.error('Authentication required. Please check your permissions.');
            }
            return;
          }
          case 403: {
            message.error('Access denied. Please check your permissions.');
            return;
          }
          default: {
            message.error(`${cutString(error.response.data.message, 60)}`);
            return;
          }
        }
      } else if (error.request) {
        message.error('Network error! Please check your connection and try again.');
      } else {
        message.error('Request error, please retry.');
      }
    },
  },
  requestInterceptors: [
    (url, options): any => {
      if (localStorage.getItem('isGuest') === 'true') {
        return { url, options };
      }

      const token = localStorage.getItem('token');
      if (token) {
        const headers = {
          ...options.headers,
          token: token,
        };
        return {
          url,
          options: { ...options, headers },
        };
      }

      const currentPath = window.location.pathname;
      if (!currentPath.includes('/login/')) {
        if (localStorage.getItem('hadToken') === 'true') {
          message.error('Your session has expired. Please log in again.');
        }
        history.push('/login/byPassword');
      }
      return { url, options };
    },
  ],
  responseInterceptors: [
    async (response) => {
      if (localStorage.getItem('isGuest') === 'true') {
        return response;
      }

      const tokenExpiring = response.headers?.['x-token-expiring'];
      const tokenExpired = response.headers?.['x-token-expired'];

      if (tokenExpired === 'true') {
        const currentPath = window.location.pathname;
        if (!currentPath.includes('/login/')) {
          AuthService.getInstance().handleTokenExpiration();
        }
      } else if (tokenExpiring === 'true') {
        try {
          await AuthService.getInstance().refreshToken();
        } catch (error) {
          const currentPath = window.location.pathname;
          if (!currentPath.includes('/login/')) {
            AuthService.getInstance().handleTokenExpiration();
          }
        }
      }

      return response;
    },
  ],
};
