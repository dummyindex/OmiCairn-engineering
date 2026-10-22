import * as constants from '@/constants/index';
import { request } from 'umi';

// Get geneset list
export const requestGetGenesetList = async (dataId: string) => {
  const { data: response } = await request(
    `${constants.API.dataUrl}/attached-data/get-geneset-list`,
    {
      method: 'GET',
      params: {
        space_type: constants.SpaceType.DATASPACE,
        space_id: dataId,
      },
    },
  );
  return response;
};

// Get cellset list
export const requestGetCellsetList = async (dataId: string) => {
  const response = await request(`${constants.API.dataUrl}/attached-data/get-cellset-list`, {
    method: 'GET',
    params: {
      space_type: constants.SpaceType.DATASPACE,
      space_id: dataId,
    },
  });
  return response;
};

// Get the bucket name and key for downloading dataStructore
export const requestGetDataStructureS3Info = async (dataId: string) => {
  const response = await request(`${constants.API.dataUrl}/attached-data/get-data-structure`, {
    method: 'GET',
    params: {
      space_type: constants.SpaceType.DATASPACE,
      space_id: dataId,
    },
  });
  return response;
};

// Get genesets data from S3
// AWS
const downloadData = async (presignedUrl) => {
  try {
    const response = await fetch(presignedUrl);

    if (!response.ok) {
      console.error('Error downloading:', response.statusText);
      throw new Error('Download failed');
    }

    const arrayBuffer = await response.arrayBuffer();
    return new Uint8Array(arrayBuffer);
  } catch (error) {
    console.error('Error downloading:', error);
    throw error;
  }
};

// Download genesets data from the bucket
export const loadGeneset = async (dataId: string) => {
  const { data: information } = await requestGetGenesetList(dataId);

  if (!information) {
    return null;
  }

  const downloadPromises = information.map(async ({ url }) => {
    try {
      const result: any = await downloadData(url);
      return result;
    } catch (error) {
      console.error('Error downloading:', error);
      throw error;
    }
  });
  const genesetNameList = information.map(({ name }) => name);

  try {
    const downloadResults = await Promise.all(downloadPromises);
    const textResults = downloadResults.map((uint8Array) => {
      const text = new TextDecoder().decode(uint8Array);
      return text;
    });
    const genesets = {};
    for (let i = 0; i < genesetNameList.length; i++) {
      const key = genesetNameList[i];
      const value = JSON.parse(textResults[i]);
      genesets[key] = value;
    }
    return genesets;
  } catch (error) {
    console.error(error);
  }
};

// Download cellsets data from the bucket
export const loadCellsets = async (dataId: string) => {
  const responseContent = await requestGetCellsetList(dataId);
  const { data: information } = responseContent;

  if (!information) {
    return null;
  }

  const downloadPromises = information.map(async (item) => {
    try {
      const result: any = await downloadData(item.url);
      return result;
    } catch (error) {
      console.error('Error downloading:', error);
      throw error;
    }
  });
  const genesetNameList = information.map(({ name }) => name);

  try {
    const downloadResults = await Promise.all(downloadPromises);
    const textResults = downloadResults.map((uint8Array) => {
      const text = new TextDecoder().decode(uint8Array);
      return text;
    });
    const cellsets = {};
    for (let i = 0; i < genesetNameList.length; i++) {
      const key = genesetNameList[i];
      const value = JSON.parse(textResults[i]);
      cellsets[key] = value;
    }
    return cellsets;
  } catch (error) {
    console.error(error);
  }
};

// Download dataStructore data
export const requestGetDataStructure = async (dataId: string) => {
  const responseContent = await requestGetDataStructureS3Info(dataId);
  const { data: information } = responseContent;
  if (!information) {
    return null;
  }
  return information;
};

// Get dynamic tags
export const requestGetTagList = async (dataId: string) => {
  const { data: response } = await request(`${constants.API.dataUrl}/attached-data/get-tag-list`, {
    method: 'GET',
    params: {
      space_type: 'data-space',
      space_id: dataId,
    },
  });
  if (Array.isArray(response)) {
    return response;
  }
  return [];
};

// Get figure bucket data under a dynamic tag
export const requestGetFigureInfo = async (figureUuid: string, thumbnail: boolean = false) => {
  const { data: response } = await request(
    `${constants.API.dataUrl}/attached-data/get-figure-download-info`,
    {
      method: 'GET',
      params: {
        figure_uuid: figureUuid,
        thumbnail: thumbnail ? '1' : '0',
      },
    },
  );
  return response;
};

// Get obs categorization results
export const requestGetDataStructureClassification = async (dataId: string) => {
  const { data: response } = await request(
    `${constants.API.dataUrl}/attached-data/get-updated-record`,
    {
      method: 'GET',
      params: {
        space_id: dataId,
      },
    },
  );
  return response;
};
