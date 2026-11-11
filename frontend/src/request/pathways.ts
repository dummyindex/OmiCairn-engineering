import { API } from '@/constants';
import { request } from 'umi';

// Get library list by organism
export const requestLibraryNameList = async (species: string | null) => {
  const result = await request(`${API.baseUrl}/gseapy/library/list/get`, {
    method: 'GET',
    params: {
      organism: species,
    },
  }).catch(() => null);
  return result;
};

export const requestPathwaysOrganismList = async () => {
  const result = await request(`${API.baseUrl}/gseapy/organism/list/get`, {
    method: 'GET',
  });
  return result;
};
