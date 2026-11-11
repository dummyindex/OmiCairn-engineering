import * as constants from '@/constants/index';
import { request } from 'umi';

export const requestPublicAnalysisList = async () => {
  const result = await request(`${constants.API.baseUrl}analysis/public/get-list`, {
    skipErrorHandler: true,
  });
  return result;
};

export const requestAnalysisList = async () => {
  const result = await request(`${constants.API.baseUrl}analysis/get-list`, {
    skipErrorHandler: true,
  });
  return result;
};

export const requestAnalysisCreate = async (
  name: string,
  description = '',
  creationSource?: string,
) => {
  const formData = new FormData();
  formData.append('name', name);
  formData.append('description', description);
  if (creationSource) {
    formData.append('creation_source', creationSource);
  }
  const result = await request(`${constants.API.baseUrl}analysis/create`, {
    skipErrorHandler: true,
    method: 'POST',
    data: formData,
  });
  return result;
};

export const requestPublickAnalysisDetail = async (analysisId: string | number) => {
  const result = await request(`${constants.API.baseUrl}analysis/public/get-info`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

export const requestAnalysisDetail = async (analysisId: string | number) => {
  const result = await request(`${constants.API.baseUrl}analysis/get-info`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

export const requestImportDatas = async (analysisId: string | number, dataIds: string[]) => {
  const result = await request(`${constants.API.baseUrl}analysis/data/import`, {
    method: 'POST',
    data: {
      analysis_id: analysisId,
      data_ids: dataIds,
    },
  });
  return result;
};

export const requestUnImportDatas = async (
  analysisId: string | number,
  dataId: string | number,
) => {
  const result = await request(`${constants.API.baseUrl}analysis/data/unimport`, {
    method: 'DELETE',
    params: {
      analysis_id: analysisId,
      data_id: dataId,
    },
  });
  return result;
};

// Edit analysis
export const requestEditAnalysis = async (analysisId: string | number, postData: any) => {
  const result = await request(`${constants.API.baseUrl}analysis/edit`, {
    method: 'POST',
    params: {
      analysis_id: analysisId,
    },
    data: postData,
  });
  return result;
};
// Copy analysis
export const requestCopyAnalysis = async (
  analysisId: string | number,
  name: string | null,
  description: string,
) => {
  const result = await request(`${constants.API.baseUrl}analysis/copy`, {
    method: 'POST',
    data: {
      analysis_id: analysisId,
      name: name,
      description,
    },
  });
  return result;
};

// Delete analysis
export const requestDeleteAnalysis = async (analysisId: string | number) => {
  const result = await request(`${constants.API.baseUrl}analysis/delete`, {
    method: 'DELETE',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

// Get the latest update record of an analysis
export const requestAnalysisUpdatedRecord = async (analysisId: string | number) => {
  const result = await request(`${constants.API.baseUrl}analysis/get-updated-record`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};

// Set whether public
export const requestToggleAnalysisPublishState = async (
  analysisId: string | number,
  isPublic: boolean,
) => {
  const shareToAll = isPublic ? 1 : 0;
  const response = await request(`${constants.API.baseUrl}analysis/toggle-sharing-for-all`, {
    method: 'POST',
    params: {
      analysis_id: analysisId,
      share_to_all: shareToAll,
    },
  });
  return response;
};

// Verify user identity
export const requestAnalysisUserRelation = async (analysisId: string | number) => {
  const response = await request(`${constants.API.baseUrl}/analysis/get-authority`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return response;
};

// Invite collaborator
export const requestInviteCollaboration = async (
  analysisId: string | number,
  receiverIdList: (string | number)[],
  permission: string | number,
) => {
  const response = await request(`${constants.API.baseUrl}/analysis/invite-collaborator`, {
    method: 'POST',
    data: {
      analysis_id: analysisId,
      receiver_id_list: receiverIdList,
      permission,
    },
  });
  return response;
};

// Remove collaborator
export const requestCancelCollaboration = async (invitation_id: string | number) => {
  const response = await request(`${constants.API.baseUrl}/analysis/cancel-collaboration`, {
    method: 'GET',
    params: {
      invitation_id,
    },
  });
  return response;
};

// Get collaborator list
export const requestCollaborationList = async (analysisId: string | number) => {
  const response = await request(`${constants.API.baseUrl}/analysis/get-collaboration-list`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });
  return response;
};

// Get collaboration invitation list
export const requestAnalysisInvitationList = async (page: number) => {
  const offset = (page - 1) * 20;
  const limit = 20;
  const res = await request(`${constants.API.baseUrl}analysis/get-invitation-list`, {
    method: 'GET',
    params: {
      offset,
      limit,
    },
  });
  return res;
};

// Accept collaboration invitation
export const requestAcceptCollaboration = async (invitation_id: string | number) => {
  const response = await request(`${constants.API.baseUrl}/analysis/accept-invitation`, {
    method: 'GET',
    params: {
      invitation_id,
    },
  });
  return response;
};

// Decline collaboration invitation
export const requestRejectCollaboration = async (invitation_id: string | number) => {
  const response = await request(`${constants.API.baseUrl}/analysis/reject-invitation`, {
    method: 'GET',
    params: {
      invitation_id,
    },
  });
  return response;
};

// Change collaborator permissions
export const requestChangePermission = async (
  invitation_id: string | number,
  permission: string,
) => {
  const response = await request(`${constants.API.baseUrl}/analysis/change-permission`, {
    method: 'POST',
    params: {
      invitation_id,
      permission,
    },
  });
  return response;
};

// Records that the current user opened an analysis; feeds the "last visited" sort on the home page.
export const requestRecordAnalysisOpened = async (analysisId: string) => {
  const result = await request(`${constants.API.baseUrl}burial-point/record-open-ap`, {
    method: 'POST',
    params: {
      analysis_id: analysisId,
    },
  });
  return result;
};
