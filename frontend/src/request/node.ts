import { API } from '@/constants';
import { NodeListFetchMode } from '@/constants/node';
import { request } from 'umi';

export const requestNodeListOfAnalysis = async (analysisId: string | null) => {
  const result = await request(`${API.baseUrl}/node/list/get`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
      mode: NodeListFetchMode.ANALYSIS,
    },
  });
  return result;
};

export const requestNodePreviteStateDict = async (analysisId: string | null) => {
  const result = await request(`${API.baseUrl}/node/get-previte-state-dict`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

export const requestNodeListByIdx = async (idx: number[]) => {
  const result = await request(`${API.baseUrl}/node/list/get`, {
    method: 'GET',
    params: {
      node_id_list: idx,
      mode: NodeListFetchMode.IDX,
    },
  });
  return result;
};

export const requestNodeByComputationId = async (computationId: string | number) => {
  const result = await request(`${API.baseUrl}/node/get-by-computation`, {
    method: 'GET',
    params: {
      computation_id: computationId,
    },
  });
  return result;
};

export const requestCreateNode = async (
  nodeType: string,
  x: number,
  y: number,
  analysisId?: string | null,
  dataId?: string | null,
  functionBlockId?: string,
  name?: string,
) => {
  const postForm = new FormData();
  postForm.append('node_type', nodeType);
  postForm.append('x', x.toString());
  postForm.append('y', y.toString());
  postForm.append('analysis_id', analysisId?.toString() || '');
  postForm.append('data_id', dataId?.toString() || '');
  postForm.append('function_block_id', functionBlockId?.toString() || '');
  postForm.append('name', name || '');

  const result = await request(`${API.baseUrl}/node/create`, {
    method: 'POST',
    data: postForm,
  });
  return result;
};

// Move a single node
export const requestUpdateNodePosition = async (nodeId: string, x: string, y: string) => {
  const result = await request(`${API.baseUrl}/node/edit`, {
    method: 'POST',
    params: {
      node_id: nodeId,
    },
    data: {
      x: x,
      y: y,
    },
  });
  return result;
};

// Move a list of nodes
export const requestUpdateNodePositionList = async (targetList: any[]) => {
  const result = await request(`${API.baseUrl}/node/batch-move`, {
    method: 'POST',
    data: {
      target_list: targetList,
    },
  });
  return result;
};

export const requestDeleteNode = async (nodeId: string) => {
  const result = await request(`${API.baseUrl}/node/delete`, {
    method: 'DELETE',
    params: {
      node_id: nodeId,
    },
  });
  return result;
};

export const requestEditNodeName = async (nodeId: string, name: string) => {
  const postForm = new FormData();
  postForm.append('node_id', nodeId);
  postForm.append('name', name);
  const result = await request(`${API.baseUrl}/node/edit`, {
    method: 'POST',
    params: {
      node_id: nodeId,
    },
    data: {
      name: name,
    },
  });
  return result;
};

export const requestEditNodeTag = async (nodeId: string, name: string) => {
  const result = await request(`${API.baseUrl}/node/edit`, {
    method: 'POST',
    params: {
      node_id: nodeId,
    },
    data: {
      tag: name,
    },
  });
  return result;
};

export const requestEditNodeParams = async (nodeId: string, params: any) => {
  const result = await request(`${API.baseUrl}/node/edit`, {
    method: 'POST',
    params: {
      node_id: nodeId,
    },
    data: {
      computation_params: params,
    },
  });
  return result;
};

export const requestNodeParams = async (nodeId: string) => {
  const result = await request(`${API.baseUrl}/node/params/get`, {
    method: 'GET',
    params: {
      node_id: nodeId,
    },
  });
  return result;
};

export const requestNodeParamFiles = async (nodeId: string) => {
  const result = await request(`${API.baseUrl}/node/list-params-files`, {
    method: 'GET',
    params: {
      node_id: nodeId,
    },
  });
  return result;
};

export const requestCopyNode = async (nodeId: string, withEdges: boolean) => {
  const result = await request(`${API.baseUrl}/node/copy`, {
    method: 'GET',
    params: {
      node_id: nodeId,
      with_edges: withEdges ? '1' : '0',
    },
  });
  return result;
};

// Reset node parameters to their initial state
export const requestRestore = async (nodeId: string) => {
  const postForm = new FormData();
  postForm.append('node_id', nodeId);
  const result = await request(`${API.baseUrl}node/params/restore`, {
    method: 'POST',
    data: postForm,
  });
  return result;
};

// Batch-delete nodes
export const requestDeleteNodeList = async (nodeIdList: string[]) => {
  const result = await request(`${API.baseUrl}node/batch-delete`, {
    method: 'POST',
    data: {
      node_id_list: nodeIdList,
    },
  });
  return result;
};

// Cancel subtree computations
export const requestCancelSubtreeComputations = async (nodeId: string) => {
  const result = await request(`${API.computationServerUrl}task/cancel-branch`, {
    method: 'POST',
    params: {
      terminated_node_id: nodeId,
    },
  });
  return result;
};

// Request a presigned POST for parameter-file upload
export const requestUploadParamFile = async (
  nodeId: string,
  filename: string,
  fileSize: number,
) => {
  const result = await request(`${API.baseUrl}node/request-upload-param-file`, {
    method: 'GET',
    params: {
      node_id: nodeId,
      file_name: filename,
      file_size: fileSize,
    },
  });
  return result;
};

// Request a presigned GET for parameter-file download
export const requestDownloadParamFile = async (nodeId: string, fileName: string) => {
  const result = await request(`${API.baseUrl}node/request-download-param-file`, {
    method: 'GET',
    params: {
      node_id: nodeId,
      file_name: fileName,
    },
  });
  return result;
};

// Delete parameter file
export const requestDeleteParamFile = async (nodeId: string, fileName: string) => {
  const result = await request(`${API.baseUrl}node/delete-param-file`, {
    method: 'DELETE',
    params: {
      node_id: nodeId,
      file_name: fileName,
    },
  });
  return result;
};

// AI fill params
export const requestFillParams = async (nodeId: string, paramDict: any, history: any) => {
  const result = await request(`${API.baseUrl}gpt/fill-params`, {
    method: 'POST',
    data: {
      param_dict: paramDict,
      history: history,
      node_id: nodeId,
    },
  });
  return result;
};

// Bug fixer fill params and result
export const requestBugFixerCodeResult = async (nodeId: string, history: any) => {
  const result = await request(`${API.baseUrl}gpt/fill-params`, {
    method: 'POST',
    data: {
      node_id: nodeId,
      history: history,
      to_create_function: '1',
    },
  });
  return result;
};

export const requestTriggerBugFixer = async (
  nodeId: string,
  maxDebug: number,
  llmModel: string,
  userPrompot: string,
) => {
  const result = await request(`${API.computationServerUrl}/computation/trigger-retry-process`, {
    method: 'POST',
    data: {
      node_id: nodeId,
      user_prompt: userPrompot,
      max_debug: maxDebug,
      llm_model: llmModel,
    },
  });
  return result;
};

export const requestNodeInfo = async (node_id: string | number) => {
  const { data: response } = await request(`${API.baseUrl}/node/get-info`, {
    method: 'GET',
    params: {
      node_id: node_id,
    },
  });
  return response;
};

export const requestGetNodeInformation = async (nodeId: string) => {
  const result = await request(`${API.baseUrl}/node/get-information`, {
    method: 'GET',
    params: {
      node_id: nodeId,
    },
  });
  return result;
};

export const requestMiniToolTruckNode = async (functionBlockId: string | number) => {
  const result = await request(`${API.baseUrl}node/get-mini-tool-node`, {
    method: 'GET',
    params: {
      function_block_id: functionBlockId,
    },
  });
  return result;
};

export const requestGenerateSingleNodeReport = async (nodeId: string, history: any) => {
  const result = await request(`${API.baseUrl}gpt/generate-node-report`, {
    method: 'POST',
    data: {
      node_id: nodeId,
      history: history,
    },
  });
  return result;
};

export const requestGenerateBranchReport = async (branchData: {
  reportNode: any;
  analysisId: string;
  branchNodes: {
    id: string;
    name: string;
    state: string;
  }[];
  model?: string;
}) => {
  const result = await request(`${API.baseUrl}gpt/generate-branch-report`, {
    method: 'POST',
    timeout: 1000 * 60 * 30,
    data: {
      report_node: branchData.reportNode,
      analysis_id: branchData.analysisId,
      branch_nodes: branchData.branchNodes,
      model: branchData.model || 'gpt-4o-mini',
    },
  });
  return result;
};

export const requestGenerateBranchReportAutomated = async (branchData: {
  reportNode: any;
  analysisId: string;
  branchNodes: {
    id: string;
    name: string;
    state: string;
  }[];
  model?: string;
}) => {
  const result = await request(`${API.baseUrl}gpt/generate-branch-report-automated`, {
    method: 'POST',
    timeout: 1000 * 60 * 30,
    data: {
      report_node: branchData.reportNode,
      analysis_id: branchData.analysisId,
      branch_nodes: branchData.branchNodes,
      model: branchData.model || 'gpt-4o-mini',
    },
  });
  return result;
};

export const requestGetBranchReportPresignedUrl = async (reportId: string) => {
  const result = await request(`${API.baseUrl}gpt/get-branch-report-presigned-url`, {
    method: 'GET',
    params: {
      report_id: reportId,
    },
  });
  return result;
};

export const requestEditComputationResourceConfig = async (
  nodeId: string,
  _computationResourceConfigure: any,
  _systemEnv: string,
) => {
  let computationResourceConfigure = _computationResourceConfigure;
  if (typeof computationResourceConfigure === 'object') {
    computationResourceConfigure = JSON.stringify(computationResourceConfigure);
  }
  const result = await request(`${API.baseUrl}node/edit`, {
    method: 'POST',
    params: {
      node_id: nodeId,
    },
    data: {
      computation_resource_configure: computationResourceConfigure,
      system_env: _systemEnv,
    },
  });
  return result;
};

export const requestCreateDynamicGeneration = async (
  previousNodeId: string,
  maxNode: number,
  maxBranch: number,
  maxDebug: number,
  userRequest: string,
  computationResourceConfigure: any,
  generationMode: string,
  LLMModel: string,
  version: string,
  replanCountLimit: string | number | null,
) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/create`, {
    method: 'POST',
    data: {
      previous_node_id: previousNodeId,
      max_node: maxNode,
      max_branch: maxBranch,
      max_debug: maxDebug,
      user_request: userRequest,
      computation_resource_configure:
        typeof computationResourceConfigure === 'object'
          ? JSON.stringify(computationResourceConfigure)
          : computationResourceConfigure,
      generation_mode: generationMode,
      llm_model: LLMModel,
      version: version,
      replan_count_limit: replanCountLimit,
    },
  });
  return result;
};

export const requestDynamicGenerationFileUploadInfo = async (generationId, file: any) => {
  const response = await request(
    `${API.computationServerUrl}dynamic-generation/get-file-upload-info`,
    {
      method: 'GET',
      params: {
        dynamic_generation_id: generationId,
        file_name: file.name,
      },
    },
  );
  return response;
};

export const requestLaunchDynamicGeneration = async (dynamicGenerationId: string) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/launch`, {
    method: 'POST',
    params: {
      dynamic_generation_id: dynamicGenerationId,
    },
  });
  return result;
};

export const requestDynamicGenerationContext = async (
  dynamicGenerationId: string | null,
  nodeId: string,
) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/get-log`, {
    method: 'GET',
    params: {
      dynamic_generation_id: dynamicGenerationId,
      node_id: nodeId,
    },
  });
  return result;
};

export const requestCreateVisualizer = async (
  originalNodeId: string,
  maxCount: number,
  userRequest: string,
  computationResourceConfigure: any,
) => {
  const result = await request(`${API.computationServerUrl}visualizer/create`, {
    method: 'POST',
    data: {
      original_node_id: originalNodeId,
      max_count: maxCount,
      user_request: userRequest,
      computation_resource_configure:
        typeof computationResourceConfigure === 'object'
          ? JSON.stringify(computationResourceConfigure)
          : computationResourceConfigure,
    },
  });
  return result;
};

export const requestLaunchingVisualizer = async (visualizerId: string) => {
  const result = await request(
    `${API.computationServerUrl}visualizer/launch?visualizer_id=${visualizerId}`,
    {
      method: 'POST',
    },
  );
  return result;
};

export const requestLaunchVisualizerAgent = async (
  nodeId: string,
  model: string,
  demand: string,
  figureCounts: number,
) => {
  const result = await request(`${API.computationServerUrl}visualizer/launch-agent`, {
    method: 'POST',
    data: {
      node_id: nodeId,
      model: model,
      demand: demand,
      figure_counts: figureCounts,
    },
  });
  return result;
};

export const requestCreateDynamicGenerationPlan = async (
  previousNodeId: string,
  maxNode: number,
  maxBranch: number,
  maxDebug: number,
  userRequest: string,
  computationResourceConfigure: any,
  generationMode: string,
  LLMModel: string,
  version: string,
  replanCountLimit: string | number | null,
  fileList: any[],
  claudeModel?: string,
  maxIterations?: number,
) => {
  const data: any = {
    previous_node_id: previousNodeId,
    max_node: maxNode,
    max_branch: maxBranch,
    max_debug: maxDebug,
    user_request: userRequest,
    computation_resource_configure:
      typeof computationResourceConfigure === 'object'
        ? JSON.stringify(computationResourceConfigure)
        : computationResourceConfigure,
    generation_mode: generationMode,
    llm_model: LLMModel,
    version: version,
    replan_count_limit: replanCountLimit,
    file_list: fileList,
  };

  if (claudeModel) {
    data.claude_execution_model = claudeModel;
  }
  if (maxIterations) {
    data.claude_max_iterations = maxIterations;
  }

  const result = await request(`${API.computationServerUrl}dynamic-generation/generate-plan`, {
    method: 'POST',
    data,
  });
  return result;
};

export const requestCreateCustomPlan = async (
  previousNodeId: string,
  maxNode: number,
  maxBranch: number,
  maxDebug: number,
  userRequest: string,
  computationResourceConfigure: any,
  generationMode: string,
  LLMModel: string,
  version: string,
  replanCountLimit: string | number | null,
  planName: string,
  planSteps: string,
  claudeModel?: string,
  maxIterations?: number,
) => {
  const data: any = {
    previous_node_id: previousNodeId,
    max_node: maxNode,
    max_branch: maxBranch,
    max_debug: maxDebug,
    user_request: userRequest,
    computation_resource_configure:
      typeof computationResourceConfigure === 'object'
        ? JSON.stringify(computationResourceConfigure)
        : computationResourceConfigure,
    generation_mode: generationMode,
    llm_model: LLMModel,
    version: version,
    replan_count_limit: replanCountLimit,
    plan_name: planName,
    plan_steps: planSteps,
  };

  if (claudeModel) {
    data.claude_execution_model = claudeModel;
  }
  if (maxIterations) {
    data.claude_max_iterations = maxIterations;
  }

  const result = await request(`${API.computationServerUrl}dynamic-generation/create-custom-plan`, {
    method: 'POST',
    data,
  });
  return result;
};

export const requestDynamicGenerationPlanList = async (analysisId: string) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/list-plans`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

export const requestDynamicGenerationPlanGet = async (
  previousNodeId: string,
  generationId: string,
) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/get-plan`, {
    method: 'GET',
    params: {
      previous_node_id: previousNodeId,
      generation_id: generationId,
    },
  });
  return result;
};

export const requestDynamicGenerationPlanUpdate = async (
  previousNodeId: string,
  generationId: string,
  attrs: Record<string, any>,
) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/update-plan`, {
    method: 'PUT',
    data: {
      previous_node_id: previousNodeId,
      generation_id: generationId,
      ...attrs,
    },
  });
  return result;
};

export const requestDynamicGenerationPlanDelete = async (
  generationId: string,
  previousNodeId: string,
) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/delete-plan`, {
    method: 'DELETE',
    params: {
      generation_id: generationId,
      previous_node_id: previousNodeId,
    },
  });
  return result;
};

export const requestContinueDynamicGeneration = async (generationId: string, nodeId: string) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/continue`, {
    method: 'POST',
    params: {
      dynamic_generation_id: generationId,
      node_id: nodeId,
    },
  });
  return result;
};

export const requestGetDynamicGeneration = async (dynamicGenerationId: string) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/get`, {
    method: 'GET',
    params: {
      dynamic_generation_id: dynamicGenerationId,
    },
  });
  return result;
};

export const requestCreateDynamicGenerationWithPlan = async (
  dynamicGenerationId: string,
  previousNodeId: string,
) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/create-with-plan`, {
    method: 'POST',
    data: {
      dynamic_generation_id: dynamicGenerationId,
      previous_node_id: previousNodeId,
    },
  });
  return result;
};

export const requestLaunchDynamicGenerationWithPlan = async (dynamicGenerationId: string) => {
  const result = await request(`${API.computationServerUrl}dynamic-generation/launch-with-plan`, {
    method: 'POST',
    params: {
      dynamic_generation_id: dynamicGenerationId,
    },
  });
  return result;
};

export const requestLaunchDynamicGenerationWithClaudeCode = async (
  dynamicGenerationId: string,
  previousNodeId: string,
) => {
  const result = await request(
    `${API.computationServerUrl}dynamic-generation/launch-with-claude-code`,
    {
      method: 'POST',
      data: {
        dynamic_generation_id: dynamicGenerationId,
        previous_node_id: previousNodeId,
      },
    },
  );
  return result;
};

export const requestPreviousNodeList = async (nodeId: string, withSelf: boolean = false) => {
  const result = await request(`${API.baseUrl}/node/get-previous-node-list`, {
    method: 'GET',
    params: {
      node_id: nodeId,
      with_self: withSelf ? '1' : '0',
    },
  });
  return result;
};

export const requestSelectFiguresAutomated = async (selectionData: {
  analysisId: string;
  branchNodes: any[];
  model?: string;
}) => {
  const result = await request(`${API.baseUrl}gpt/select-figures-automated`, {
    method: 'POST',
    timeout: 1000 * 60 * 5,
    data: {
      analysis_id: selectionData.analysisId,
      branch_nodes: selectionData.branchNodes,
      model: selectionData.model || 'gpt-4o-mini',
    },
  });
  return result;
};
