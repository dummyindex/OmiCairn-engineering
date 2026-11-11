import * as constants from '@/constants/index';
import { request } from 'umi';

export const getAPIKeys = async () => {
  const response = await request(`${constants.API.baseUrl}/api-key/list-keys`, {
    method: 'GET',
  });
  return response;
};

export const createAPIKey = async (data: { name: string; value: string }) => {
  const response = await request(`${constants.API.baseUrl}/api-key/create-key`, {
    method: 'POST',
    data,
  });
  return response;
};

export const updateAPIKey = async (
  api_key_id: string,
  data: {
    name: string;
    value: string;
  },
) => {
  const response = await request(
    `${constants.API.baseUrl}/api-key/update-key?key_id=${api_key_id}`,
    {
      method: 'POST',
      data,
    },
  );
  return response;
};

export const deleteAPIKey = async (api_key_id: string) => {
  const response = await request(
    `${constants.API.baseUrl}/api-key/delete-key?key_id=${api_key_id}`,
    {
      method: 'DELETE',
    },
  );
  return response;
};
