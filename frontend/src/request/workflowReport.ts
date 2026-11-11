import { API } from '@/constants';
import { request } from 'umi';

export const requestWorkflowReportList = async (analysisId: string | null) => {
  if (!analysisId) {
    return { data: [] };
  }
  const result = await request(`${API.baseUrl}workflow-report/list-by-analysis`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

export const requestWorkflowReportContent = async (uuid: string, fileName: string) => {
  const { data: presignedUrl } = await request(`${API.baseUrl}workflow-report/get-presigned-url`, {
    method: 'GET',
    params: {
      uuid,
      file_name: fileName,
    },
  });
  const result = await request(presignedUrl, {
    method: 'GET',
  });
  return result;
};

export const requestUpdateWorkflowReportContent = async (
  uuid: string,
  fileName: string,
  content: string,
) => {
  const result = await request(`${API.baseUrl}workflow-report/get-presigned-post`, {
    method: 'GET',
    params: {
      uuid,
      file_name: fileName,
      file_size: content.length,
    },
  });
  const {
    presigned_url: { url, fields },
  } = result.data;
  const formData = new FormData();
  Object.entries(fields).forEach(([key, value]) => {
    formData.append(key, value);
  });
  formData.append('file', content);
  const uploadResult = await fetch(url, {
    method: 'POST',
    body: formData,
  });
  return uploadResult;
};

export const requestDeleteWorkflowReport = async (uuid: string) => {
  const result = await request(`${API.baseUrl}workflow-report/delete`, {
    method: 'DELETE',
    params: {
      uuid,
    },
  });
  return result;
};

export const requestUpdateWorkflowReportMetadata = async (uuid: string, updatedObj: any) => {
  const result = await request(`${API.baseUrl}workflow-report/edit-info`, {
    method: 'POST',
    params: {
      uuid,
    },
    data: updatedObj,
  });
  return result;
};

export const requestWorkflowReportInfo = async (uuid: string) => {
  const result = await request(`${API.baseUrl}workflow-report/get-info`, {
    method: 'GET',
    params: {
      uuid,
    },
  });
  return result;
};

export const requestCreateWorkflowReport = async (
  analysisId: string,
  computationDetailsList: any[],
  nodeIds: string[] | number[],
) => {
  const result = await request(`${API.baseUrl}gpt/create-workflow-report`, {
    method: 'POST',
    data: {
      analysis_id: analysisId,
      computation_details_list: computationDetailsList,
      node_ids: nodeIds,
    },
  });
  const { data } = result;
  // snake_case to camelCase
  const camelData = {};
  Object.keys(data).forEach((key) => {
    const newKey = key.replace(/_(\w)/g, (all, letter) => letter.toUpperCase());
    camelData[newKey] = data[key];
  });
  return camelData;
};
