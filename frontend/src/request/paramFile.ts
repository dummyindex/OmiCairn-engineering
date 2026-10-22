import { API } from '@/constants/index';
import { request } from 'umi';

export const requestCreateParamFile = async ({ name, size }: { name: string; size: number }) => {
  const res = await request(`${API.baseUrl}param-file/create-file`, {
    method: 'POST',
    params: {
      name,
      size,
    },
  });

  return res;
};

export const requestRemoveParamFile = async (uuid: string) => {
  const res = await request(`${API.baseUrl}param-file/remove-file`, {
    method: 'DELETE',
    params: {
      uuid,
    },
  });

  return res;
};

export const requestListParamFiles = async ({
  offset,
  limit,
  searchKey,
}: {
  offset: number;
  limit: number;
  searchKey: string;
}) => {
  const res = await request(`${API.baseUrl}param-file/list`, {
    method: 'GET',
    params: {
      offset,
      limit,
      searchKey,
    },
  });

  return res;
};

export const requestParamFileInfo = async (uuid: string) => {
  const res = await request(`${API.baseUrl}param-file/get-info`, {
    method: 'GET',
    params: {
      uuid,
    },
  });

  return res;
};

export const requestListParamFilesInfo = async (uuids: string[]) => {
  const res = await request(`${API.baseUrl}param-file/get-list-info`, {
    method: 'POST',
    data: {
      uuids,
    },
  });

  return res;
};

export const requestListParamFilesBySuffixes = async (suffixes: string[]) => {
  const res = await request(`${API.baseUrl}param-file/list-by-suffixes`, {
    method: 'POST',
    data: {
      suffixes,
    },
  });

  return res;
};

export const requestParamFilePresignedUrl = async (uuid: string) => {
  const res = await request(`${API.baseUrl}param-file/get-presigned-url`, {
    method: 'GET',
    params: {
      uuid,
    },
  });

  return res;
};

export const requestUpdateParamFile = async ({
  uuid,
  updatedAttrs,
}: {
  uuid: string;
  updatedAttrs: Record<string, any>;
}) => {
  const res = await request(`${API.baseUrl}param-file/update-info`, {
    method: 'PUT',
    params: {
      uuid,
    },
    data: updatedAttrs,
  });

  return res;
};
