import { API } from '@/constants';
import { request } from 'umi';

export const requestTempUploadInfo = async (fileName: string, fileSize: number) => {
  const result = await request(
    `${API.baseUrl}sss/get-temp-upload-info?file_name=${fileName}&file_size=${fileSize}`,
    {
      skipErrorHandler: true,
      method: 'GET',
    },
  );
  return result;
};
