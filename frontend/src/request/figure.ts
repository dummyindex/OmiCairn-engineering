import { ServiceCloud } from '@/constants';
import * as constants from '@/constants/index';
import { ServiceCloudSelection } from '@/constants/serviceCloudSelection';
import { request } from 'umi';
import { requestGetFigureInfo } from './attachedData';

// AWS
// Download an image from S3 using getObject
const downloadImage = async (presignedUrl) => {
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

// Download an image from the bucket for display
export const loadFigure = async (figureUuid: string) => {
  if (ServiceCloud == ServiceCloudSelection.AWS) {
    const responseContent = await requestGetFigureInfo(figureUuid);
    if (!responseContent) {
      return null;
    }

    try {
      const imageBuffer: any = await downloadImage(responseContent);
      let binary = '';
      for (let i = 0; i < imageBuffer.length; i++) {
        binary += String.fromCharCode(imageBuffer[i]);
      }

      const base64String = window.btoa(binary);
      return base64String;
    } catch (error) {
      console.error(error);
    }
  }
};

// Get figure list
export const requestFigureList = async (computationId: string) => {
  const response = await request(`${constants.API.baseUrl}computation/figure-list/get`, {
    method: 'GET',
    params: {
      computation_id: computationId,
    },
  });
  return response;
};

export const requestListFigureV2 = async (computationId: string) => {
  const response = await request(`${constants.API.baseUrl}figure/list`, {
    method: 'GET',
    params: {
      computation_id: computationId,
    },
  });
  return response;
};

export const requestListFigureByNodeId = async (nodeId: string) => {
  const response = await request(`${constants.API.baseUrl}figure/list-by-node-id`, {
    method: 'GET',
    params: {
      node_id: nodeId,
    },
  });
  return response;
};
