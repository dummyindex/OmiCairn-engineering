import { API } from '@/constants';
import { request } from 'umi';

export const requestEdgeListOfAnalysis = async (analysisId: string | null) => {
  const result = await request(`${API.baseUrl}/edge/list/get`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

export const requestCreateEdge = async (
  sourceNodeId: number,
  targetNodeId: number,
  analysisId?: string | null,
) => {
  const postForm = new FormData();
  postForm.append('source_node_id', sourceNodeId.toString());
  postForm.append('target_node_id', targetNodeId.toString());
  postForm.append('analysis_id', analysisId?.toString() || '');

  const result = await request(`${API.baseUrl}/edge/create`, {
    method: 'POST',
    data: postForm,
  });
  return result;
};

export const requestDeleteEdge = async (edgeId: number) => {
  const result = await request(`${API.baseUrl}/edge/delete`, {
    method: 'DELETE',
    params: {
      edge_id: edgeId,
    },
  });
  return result;
};
