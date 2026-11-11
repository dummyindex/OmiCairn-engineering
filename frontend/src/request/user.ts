import { API } from '@/constants/index';
import { request } from 'umi';

export const requestSearchUser = async (searchText: string, page: number) => {
  if (!searchText) {
    return [];
  }
  const offset = (page - 1) * 10;
  const res = await request(`${API.baseUrl}user/search`, {
    method: 'GET',
    params: {
      keyword: searchText,
      offset: offset,
      limit: 50,
    },
  });

  return res;
};

export const requestEditUser = async (
  userName: string,
  email: string,
  phoneNumber: string,
  account_type: string,
) => {
  const res = await request(`${API.baseUrl}user/edit`, {
    method: 'POST',
    data: {
      user_name: userName,
      email: email,
      phone_number: phoneNumber,
      account_type: account_type,
    },
  });

  return res;
};
