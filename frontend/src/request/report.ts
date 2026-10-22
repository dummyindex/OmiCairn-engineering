import { API } from '@/constants';
import { request } from 'umi';

export const requestSubmitReport = async (
  node_id: string | number,
  summary: string,
  detail: string,
) => {
  const res = await request(`${API.baseUrl}/report/create`, {
    method: 'POST',
    data: {
      node_id,
      summary,
      detail,
    },
  });
  return res;
};
