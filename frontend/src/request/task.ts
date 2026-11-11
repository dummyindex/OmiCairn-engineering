import { API } from '@/constants';
import { request } from 'umi';

export const requestDispatchTask = async (
  analysisId: string | null,
  nodeIdList: string[] | number[],
  edgeIdList: string[] | number[],
) => {
  const result = await request(`${API.computationServerUrl}/task/dispatch`, {
    method: 'POST',
    data: {
      analysis_id: analysisId,
      node_id_list: nodeIdList,
      edge_id_list: edgeIdList,
    },
  });
  return result;
};

export const requestExtendTask = async (
  nodeIdList: string[] | number[],
  edgeIdList: string[] | number[],
) => {
  const result = await request(`${API.computationServerUrl}/task/extend`, {
    method: 'POST',
    data: {
      node_id_list: nodeIdList,
      edge_id_list: edgeIdList,
    },
  });
  return result;
};

export const requestCancelAllTask = async (analysisId: string | number | null) => {
  const result = await request(`${API.computationServerUrl}/task/cancel-by-analysis`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

export const requestInvokeCodeAgent = async (
  nodeId: string | number,
  maxDebug: number,
  model: string,
) => {
  const result = await request(`${API.computationServerUrl}/computation/invoke-code-agent`, {
    method: 'POST',
    params: {
      node_id: nodeId,
      max_debug: maxDebug,
      model: model,
    },
  });
  return result;
};
