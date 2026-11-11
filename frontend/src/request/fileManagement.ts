import * as constants from '@/constants/index';
import { request } from 'umi';

export const requestGetFileList = async (analysisId?: string | number) => {
  const result = await request(`${constants.API.baseUrl}file/list/get`, {
    skipErrorHandler: true,
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

export const requestDeleteFile = async (fileId: string) => {
  const result = await request(`${constants.API.baseUrl}file/remove`, {
    skipErrorHandler: true,
    method: 'DELETE',
    params: {
      file_id: fileId,
    },
  });
  return result;
};

export const requestUploadFile = async (analysisId: string | number, file: File) => {
  const formData = new FormData();
  formData.append('analysis_id', analysisId.toString());
  formData.append('file', file);

  const result = await request(`${constants.API.baseUrl}file/upload`, {
    skipErrorHandler: true,
    method: 'POST',
    data: formData,
  });
  return result;
};
