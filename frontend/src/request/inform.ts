import { API } from '@/constants/index';
import type { InformType } from '@/interfaces/inform';
import { request } from 'umi';

export const requestCreateAnnouncement = async ({
  content,
  title,
}: {
  content: string;
  title: string;
}) => {
  const res = await request(`${API.baseUrl}inform/create-announcement`, {
    method: 'POST',
    data: {
      content,
      title,
    },
  });

  return res;
};

export const requestReadAnnouncement = async (announcementId: string | number) => {
  const res = await request(`${API.baseUrl}inform/read-announcement`, {
    method: 'GET',
    params: {
      announcement_id: announcementId,
    },
  });

  return res;
};

export const requestListAnnouncement = async (page: number) => {
  const offset = (page - 1) * 20;
  const limit = 20;
  const res = await request(`${API.baseUrl}inform/list-announcement`, {
    method: 'GET',
    params: {
      offset,
      limit,
    },
  });

  return res;
};

export const requestListUnreadAnnouncement = async () => {
  const res = await request(`${API.baseUrl}inform/list-unread-announcement`, {
    method: 'GET',
  });

  return res;
};

export const requestAnnouncementDetail = async (announcementId: string | number) => {
  const res = await request(`${API.baseUrl}inform/get-announcement-detail`, {
    method: 'GET',
    params: {
      announcement_id: announcementId,
    },
  });

  return res;
};

export const requestListInform = async (
  page: number | string,
  informType: InformType | null = null,
) => {
  const offset = (+page - 1) * 20;
  const limit = 20;
  const params: any = {
    offset,
    limit,
  };
  if (!!informType) {
    params.inform_type = informType;
  }
  const res = await request(`${API.baseUrl}inform/list-inform`, {
    method: 'GET',
    params: params,
  });

  return res;
};

export const requestListUnreadInform = async (offset: number, limit: number) => {
  if (limit <= 0) {
    throw new Error('Limit must be greater than 0');
  }
  const res = await request(`${API.baseUrl}inform/list-unread-inform`, {
    method: 'GET',
    params: {
      offset: offset,
      limit,
    },
  });

  return res;
};

export const requestInformDetail = async (informId: string | number) => {
  const res = await request(`${API.baseUrl}inform/get-inform-detail`, {
    method: 'GET',
    params: {
      inform_id: informId,
    },
  });

  return res;
};

export const requestReadInform = async (informIdList: (string | number)[]) => {
  const res = await request(`${API.baseUrl}inform/read-inform`, {
    method: 'POST',
    data: {
      inform_id_list: informIdList,
    },
  });

  return res;
};

export const requestInformCount = async () => {
  const res = await request(`${API.baseUrl}inform/get-inform-count`, {
    method: 'GET',
  });

  return res;
};

export const requestUnreadAnnouncementList = async () => {
  const res = await request(`${API.baseUrl}inform/list-unread-announcement`, {
    method: 'GET',
  });

  return res;
};
