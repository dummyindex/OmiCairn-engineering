import { API } from '@/constants';
import { request } from 'umi';

export const requestVisualData = async (dataId: string, demand: any, signal: any = null) => {
  const result = await request(`${API.dataUrl}/visualization/data/get`, {
    method: 'POST',
    data: {
      data_id: dataId,
      demand: demand,
    },
    signal,
  });
  return result;
};

export const requestEditVisualData = async (dataId: string, demand: any, signal: any = null) => {
  const result = await request(`${API.dataUrl}/visualization/data/edit`, {
    method: 'POST',
    data: {
      data_id: dataId,
      demand: demand,
    },
    signal,
  });
  return result;
};

export const requestDeleteVisualData = async (dataId: string, demand: any, signal: any = null) => {
  const result = await request(`${API.dataUrl}/visualization/data/delete`, {
    method: 'POST',
    data: {
      data_id: dataId,
      demand: demand,
    },
    signal,
  });
  return result;
};

export const requestRenameVisualData = async (dataId: string, demand: any, signal: any = null) => {
  const result = await request(`${API.dataUrl}/visualization/data/rename`, {
    method: 'POST',
    data: {
      data_id: dataId,
      demand: demand,
    },
    signal,
  });
  return result;
};

export const requestAddVisualData = async (dataId: string, demand: any, signal: any = null) => {
  const result = await request(`${API.dataUrl}/visualization/data/add`, {
    method: 'POST',
    data: {
      data_id: dataId,
      demand: demand,
    },
    signal,
  });
  return result;
};
