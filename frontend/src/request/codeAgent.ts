import { API } from '@/constants/index';
import { request } from 'umi';

/**
 * Get the code agent message list
 */
export const requestGetCodeAgentMessageList = async (params: {
  computation_id: string;
  offset?: number;
  limit?: number;
}) => {
  const res = await request(`${API.computationServerUrl}/code-agent-proxy/message/list`, {
    method: 'GET',
    params,
  });

  return res;
};

/**
 * Get message content (via presigned URL)
 */
export const requestGetMessageContent = async (presignedUrl: string) => {
  const response = await fetch(presignedUrl);
  if (!response.ok) {
    throw new Error('Failed to fetch message content');
  }
  return response.json();
};

export const requestCodeAgentToolRecord = async (params: { computation_id: string }) => {
  const res = await request(`${API.computationServerUrl}/code-agent-proxy/get-action-records`, {
    method: 'GET',
    params,
  });

  return res;
};
