import { API } from '@/constants/index';
import { request } from 'umi';

export const requestPipelineCollect = async (
  name: string,
  groupName: string,
  description: string,
  nodeIdList: string[],
  edgeIdList: string[],
) => {
  const res = await request(`${API.baseUrl}pipeline-template/create`, {
    method: 'POST',
    data: {
      name: name,
      group_name: groupName,
      description: description,
      node_id_list: nodeIdList,
      edge_id_list: edgeIdList,
    },
  });
  return res;
};

// Fetch group list
export const requestGroupPipelineGet = async () => {
  const res = await request(`${API.baseUrl}pipeline-template/group-name/list/get`, {
    method: 'GET',
  });
  return res;
};

// Fetch pipeline list
export const requestPipelineTemplateList = async (groupName: string) => {
  const res = await request(`${API.baseUrl}pipeline-template/list/get`, {
    method: 'GET',
    params: {
      group_name: groupName,
    },
  });
  return res;
};

// Edit group API
export const requestEditPipelineTemplateGroup = async (oldName: string, name: string) => {
  const res = await request(`${API.baseUrl}pipeline-template/group-name/edit`, {
    method: 'POST',
    data: {
      old_name: oldName,
      new_name: name,
    },
  });
  return res;
};

// Delete group API
export const requestDeletePipelineTemplateGroup = async (groupName: string) => {
  const res = await request(`${API.baseUrl}pipeline-template/group/remove`, {
    method: 'DELETE',
    params: {
      group_name: groupName,
    },
  });
  return res;
};

//Delete pipelineTemplate API
export const requestDeletePipelineTemplate = async (pipelineId: string) => {
  const res = await request(`${API.baseUrl}pipeline-template/remove`, {
    method: 'DELETE',
    params: {
      pipeline_template_id: pipelineId,
    },
  });
  return res;
};

//Edit pipelineTemplate API
export const requestEditPipelineTemplate = async (
  pipelineId: string,
  name: string,
  groupName: string,
) => {
  const res = await request(`${API.baseUrl}pipeline-template/metadata/edit`, {
    method: 'POST',
    data: {
      pipeline_template_id: pipelineId,
      name: name,
      group_name: groupName,
    },
  });
  return res;
};

// Import pipelineTemplate
export const requestImportPipelineTemplate = async (pipelineId: string, analysisId: number) => {
  const res = await request(`${API.baseUrl}pipeline-template/import-into-analysis`, {
    method: 'POST',
    data: {
      pipeline_template_id: pipelineId,
      analysis_id: analysisId,
    },
  });
  return res;
};

// Fetch fb list
export const requestFBListInPT = async (pipelineId: string) => {
  const res = await request(`${API.baseUrl}pipeline-template/function-block/list/get`, {
    method: 'GET',
    params: {
      pipeline_template_id: pipelineId,
    },
  });
  return res;
};

// Two public APIs
// Fetch public list
export const requestPublicPtList = async (groupName: string) => {
  const res = await request(`${API.baseUrl}pipeline-template/public/list/get`, {
    method: 'GET',
    params: {
      group_name: groupName,
    },
  });
  return res;
};

// Public group-name list
export const requestPublicPTGroupList = async () => {
  const res = await request(`${API.baseUrl}pipeline-template/public/group-name/list/get`, {
    method: 'GET',
  });
  return res;
};
