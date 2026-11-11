import { API } from '@/constants/index';
import { request } from 'umi';

export const requestLatestComputation = async (nodeId: string) => {
  const res = await request(`${API.baseUrl}computation/latest-by-node/get`, {
    method: 'GET',
    params: {
      node_id: nodeId,
    },
  });

  return res;
};

export const requestComputationList = async (byWhat: 'node' | 'task', id: string) => {
  const id_key = `${byWhat}_id`;
  const res = await request(`${API.baseUrl}computation/list`, {
    method: 'GET',
    params: {
      mode: byWhat,
      [id_key]: id,
    },
  });

  return res;
};

export const requestDashboardList = async (analysis_id: string) => {
  const result = await request(`${API.baseUrl}node/list/get`, {
    method: 'GET',
    params: {
      mode: 'analysis',
      analysis_id,
      with_computation: 1,
    },
  });

  return result;
};

export const requestRefreshOptimizedErrorDescription = async (computationId: string) => {
  const res = await request(`${API.baseUrl}computation/optimized-error-description/refresh`, {
    method: 'GET',
    params: {
      computation_id: computationId,
    },
  });
  return res;
};

export const requestComputationGetSummary = async (computationId: string) => {
  const res = await request(`${API.computationServerUrl}computation/get-summary`, {
    method: 'GET',
    params: {
      computation_id: computationId,
    },
  });
  return res;
};

export const requestComputationGetLogs = async (computationId: string) => {
  const res = await request(`${API.computationServerUrl}computation/get-logs`, {
    method: 'GET',
    params: {
      computation_id: computationId,
    },
  });
  return res;
};

export const requestComputationOutputList = async (
  computationId: string,
  options?: {
    prefix?: string;
    start_after_file_name?: string;
    max_keys?: number;
    search_query?: string;
    file_type_filter?: string;
  },
) => {
  const res = await request(`${API.computationServerUrl}computation/list-output-files`, {
    method: 'GET',
    params: {
      computation_id: computationId,
      prefix: options?.prefix,
      start_after_file_name: options?.start_after_file_name,
      max_keys: options?.max_keys || 50,
      search_query: options?.search_query,
      file_type_filter: options?.file_type_filter,
    },
  });
  return res;
};

export const requestOutputFileDownloadInfo = async (computationId: string, key: string) => {
  const res = await request(
    `${API.computationServerUrl}computation/get-output-file-download-info`,
    {
      method: 'GET',
      params: {
        computation_id: computationId,
        object_key: key,
      },
    },
  );
  return res;
};

export const requestComputationTrail = async (nodeId: string) => {
  const res = await request(`${API.baseUrl}computation/get-former-history`, {
    method: 'GET',
    params: {
      node_id: nodeId,
    },
  });
  return res;
};

export const requestComputationDetailsList = async (nodeIds: (string | number)[]) => {
  const res = await request(`${API.baseUrl}computation/get-details-by-nodes`, {
    method: 'POST',
    data: {
      node_ids: nodeIds,
    },
  });
  return res;
};

export const requestComputationReport = async (computationId: string) => {
  const result = await request(`${API.baseUrl}computation/get-report`, {
    method: 'GET',
    params: {
      computation_id: computationId,
    },
  });
  return result;
};

export const requestStopBugFixerComputation = async (analysisId: string) => {
  const result = await request(`${API.computationServerUrl}computation/stop-retry-process`, {
    method: 'POST',
    params: {
      retry_process_id: analysisId,
    },
  });
  return result;
};

export const requestBugFixerNodeListByNode = async (nodeId: string) => {
  const result = await request(
    `${API.computationServerUrl}computation/list-retry-process-by-node`,
    {
      method: 'GET',
      params: {
        node_id: nodeId,
      },
    },
  );
  return result;
};

export const requestBugFixerNodeListByAnalysis = async (analysisId: string) => {
  const result = await request(
    `${API.computationServerUrl}computation/list-retry-process-by-analysis`,
    {
      method: 'GET',
      params: {
        analysis_id: analysisId,
      },
    },
  );
  return result;
};

export const requestBugFixerHistory = async (retryProcessId: string) => {
  const result = await request(
    `${API.computationServerUrl}computation/get-retry-process-fix-history-details`,
    {
      method: 'GET',
      params: {
        retry_process_id: retryProcessId,
      },
    },
  );
  return result;
};

export const requestRunBugFixer = async (nodeId: string, userPrompt: string) => {
  const result = await request(`${API.computationServerUrl}computation/trigger-retry-process`, {
    method: 'POST',
    params: {
      node_id: nodeId,
      user_prompt: userPrompt,
    },
  });
  return result;
};

export const requestBugFixerComputationContext = async (computationId: string) => {
  const result = await request(`${API.computationServerUrl}computation/get-retry-process-session`, {
    method: 'GET',
    params: {
      computation_id: computationId,
    },
  });
  return result;
};

export const requestBugFixerSessions = async (retryProcessId: string) => {
  const result = await request(`${API.computationServerUrl}computation/list-bug-fixer-sessions`, {
    method: 'GET',
    params: {
      retry_process_id: retryProcessId,
    },
  });
  return result;
};

export const requestDynamicGenerationListByAnalysis = async (analysisId: string) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/list-by-analysis`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

export const requestDynamicGenerationSessions = async (dynamicGenerationId: string) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/list-sessions`, {
    method: 'GET',
    params: {
      dynamic_generation_id: dynamicGenerationId,
    },
  });
  return result;
};

export const requestDynamicGenerationNodesBySession = async (
  dynamicGenerationSessionId: string,
) => {
  const result = await request(
    `${API.computationServerUrl}dynamic-generation/list-nodes-by-session`,
    {
      method: 'GET',
      params: {
        dynamic_generation_session_id: dynamicGenerationSessionId,
      },
    },
  );
  return result;
};

export const requestListOutputFolders = async (computationId: string, prefix?: string) => {
  const res = await request(`${API.computationServerUrl}computation/list-output-folders`, {
    method: 'GET',
    params: {
      computation_id: computationId,
      prefix: prefix || '',
    },
  });
  return res;
};

export const requestJobReviewerErrorDetails = async (computationId: string) => {
  const result = await request(`${API.computationServerUrl}computation/get-job-reviewer-error`, {
    method: 'GET',
    params: {
      computation_id: computationId,
    },
  });
  return result;
};

export const requestProgrammingAgentMessages = async (
  computationId: string,
  page: number = 1,
  pageSize: number = 20,
) => {
  const result = await request(
    `${API.computationServerUrl}computation/get-programming-agent-messages`,
    {
      method: 'GET',
      params: {
        computation_id: computationId,
        page,
        page_size: pageSize,
      },
    },
  );
  return result;
};
