import type { LoginResponse, UserInfo } from '@/services/auth/types';
import * as constants from '@/constants/index';
import { request } from 'umi';

const BASE_URL = constants.API.baseUrl;

export const requestUserInfo = async (): Promise<{
  code: number;
  data: UserInfo;
}> => {
  return request(`${BASE_URL}user/info/get`, {
    credentials: 'include',
    skipErrorHandler: true,
  });
};

export const requestRegisterComponent = async (
  // phoneNumber: string,
  password: string,
  userName: string,
  account_type: string,
  // authCode: string
) => {
  const formData = new FormData();
  // formData.append('phone_number', phoneNumber);
  formData.append('user_name', userName);
  formData.append('password', password);
  formData.append('account_type', account_type);
  // formData.append('auth_code', authCode);
  const response = await request(`${constants.API.baseUrl}user/register`, {
    method: 'POST',
    data: formData,
  });
  return response;
};

export const requestLoginByPassword = async (
  phoneNumber: string,
  password: string,
): Promise<LoginResponse> => {
  const formData = new FormData();
  formData.append('phone_number', phoneNumber);
  formData.append('password', password);

  return request(`${BASE_URL}user/login-by-password`, {
    method: 'POST',
    data: formData,
    credentials: 'include',
  });
};

export const requestValidateToken = async (): Promise<{
  code: number;
  data: string;
}> => {
  return request(`${BASE_URL}user/validate-token`, {
    method: 'GET',
    credentials: 'include',
  });
};
