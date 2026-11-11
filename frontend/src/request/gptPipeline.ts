import * as constants from '@/constants/index';
import { request } from 'umi';

export const requestRecommendPipeline = async (requestMessage: string) => {
  const response = await request(`${constants.API.baseUrl}gpt/recommend-pipeline`, {
    method: 'POST',
    data: {
      user_request: requestMessage,
    },
  });

  return response;
};

export const requestGeneratePipeline = async (recommendStructure, analysisId) => {
  const response = await request(`${constants.API.baseUrl}flow/generate-pipeline-by-gpt`, {
    method: 'POST',
    data: {
      recommend_structure: recommendStructure,
      analysis_id: analysisId,
    },
  });

  return response;
};

// Find similar pipelines
export const requestSimilarPT = async (requestMessage: string) => {
  const res = await request(`${constants.API.baseUrl}gpt/get-similar-pipeline-template`, {
    method: 'POST',
    data: {
      user_request: requestMessage,
    },
  });
  return res;
};
