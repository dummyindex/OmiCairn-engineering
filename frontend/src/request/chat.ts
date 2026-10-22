import * as constants from '@/constants/index';
import { request } from 'umi';

// Simple version
export const requestGetChatbotHistory = async (analysisId: string | null, ownerId: string) => {
  const response = await request(`${constants.API.baseUrl}gpt/chat/history`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
      owner_id: ownerId,
    },
  });

  return response;
};

// Global
// Chatbot initialization
export const requestGlobalInitChatbot = async (analysisId: string | null) => {
  const response = await request(`${constants.API.baseUrl}gpt/chat/init-global-chat`, {
    method: 'POST',
    params: {
      analysis_id: analysisId,
      // owner_id: ownerId,
    },
  });
  return response;
};

export const requestGlobalGetChat = async (
  analysisId: string | null,
  chatId: string,
  ownerId: string,
  message: string,
) => {
  const response = await request(`${constants.API.baseUrl}gpt/chat/send-global-message`, {
    method: 'POST',
    params: {
      analysis_id: analysisId,
      chat_id: chatId,
      owner_id: ownerId,
      message: message,
    },
  });
  return response;
};

// Local node
export const requestLocalInitChatbot = async (analysisId: string | null, nodeId: string) => {
  const response = await request(`${constants.API.baseUrl}gpt/chat/init-local-chat`, {
    method: 'POST',
    params: {
      analysis_id: analysisId,
      node_id: nodeId,
    },
  });
  return response;
};

export const requestLocalGetChat = async (
  analysisId: string | null,
  chatId: string,
  ownerId: string,
  message: string,
) => {
  const response = await request(`${constants.API.baseUrl}gpt/chat/send-local-message`, {
    method: 'POST',
    params: {
      analysis_id: analysisId,
      chat_id: chatId,
      message: message,
      owner_id: ownerId,
    },
  });
  return response;
};

// Full version
// Chatbot initialization
export const requestComplexInitChatbot = async (analysisId: string | null) => {
  const response = await request(`${constants.API.baseUrl}gpt/complex-chat/init-chat`, {
    method: 'POST',
    params: {
      analysis_id: analysisId,
    },
  });
  return response;
};

// API to restore a conversation from history
export const requestComplexRestoreList = async (threadId: string | null) => {
  const response = await request(`${constants.API.baseUrl}gpt/complex-chat/list-message`, {
    method: 'GET',
    params: {
      thread_id: threadId,
    },
  });
  return response;
};

// History list
export const requestGetComplexHistory = async (analysisId: string | null) => {
  const response = await request(`${constants.API.baseUrl}gpt/complex-chat/list-chat`, {
    method: 'GET',
    params: {
      analysis_id: analysisId,
    },
  });

  return response;
};

// Send-message API
export const requestComplexSendMessage = async (
  analysisId: string | null,
  threadId: string,
  message: string,
) => {
  const response = await request(`${constants.API.baseUrl}gpt/complex-chat/send-message`, {
    method: 'POST',
    params: {
      analysis_id: analysisId,
      thread_id: threadId,
      message: message,
    },
  });

  return response;
};

// -------------------------------------------------------------------------------------------

// v3.0 Chat API
export const requestV3ListChats = async () => {
  const response = await request(`${constants.API.baseUrl}v3.0/chat/list`, {
    method: 'GET',
  });
  return response;
};

export const requestV3CreateChat = async (
  analysis_id: number | string | null,
  model: any,
  current_node_id: any = null,
) => {
  const response = await request(`${constants.API.baseUrl}v3.0/chat/create`, {
    method: 'POST',
    data: {
      analysis_id: analysis_id,
      current_node_id: current_node_id,
      model: model,
    },
  });
  return response;
};

export const requestV3SendMessage = async (
  chatId: string,
  message: string,
  attachedFiles?: any[],
) => {
  const response = await request(`${constants.API.baseUrl}v3.0/chat/send-message`, {
    method: 'POST',
    data: {
      chat_id: chatId,
      message: message,
      fileS3Key: attachedFiles || [],
    },
  });
  return response;
};

export const requestV3CallTool = async (
  chatId: string,
  toolCallId: string,
  toolName: string,
  toolParams: any = {},
) => {
  const response = await request(`${constants.API.baseUrl}v3.0/chat/call-tool`, {
    method: 'POST',
    data: {
      chat_id: chatId,
      tool_call_id: toolCallId,
      tool_name: toolName,
      tool_params: toolParams,
    },
  });
  return response;
};

export const requestV3ChatHeartbeat = async (chatId: string, lastUpdatedTime?: string) => {
  const response = await request(`${constants.API.baseUrl}v3.0/chat/heartbeat`, {
    method: 'GET',
    params: {
      chat_id: chatId,
      last_updated_time: lastUpdatedTime,
    },
  });
  return response;
};

export const requestV3GetChatInfo = async (chatId: string) => {
  const response = await request(`${constants.API.baseUrl}v3.0/chat/get-information`, {
    method: 'GET',
    params: {
      chat_id: chatId,
    },
  });
  return response;
};

export const requestV3GetChatMessages = async (
  chatId: string,
  limit: number = 100,
  offset: number = 0,
) => {
  const response = await request(`${constants.API.baseUrl}v3.0/chat/get-messages`, {
    method: 'GET',
    params: {
      chat_id: chatId,
      limit: limit,
      offset: offset,
    },
  });
  return response;
};

export const requestV3DeleteChat = async (chatId: string) => {
  const response = await request(`${constants.API.baseUrl}v3.0/chat/delete`, {
    method: 'POST',
    data: {
      chat_id: chatId,
    },
  });
  return response;
};

export const requestV3UpdateChat = async (chatId: string, updatedAttrs: any) => {
  const response = await request(`${constants.API.baseUrl}v3.0/chat/update?chat_id=${chatId}`, {
    method: 'POST',
    data: updatedAttrs,
  });
  return response;
};

export const requestV3GetSubTaskList = async (chatId: string) => {
  const response = await request(
    `${constants.API.baseUrl}v3.0/chat/list-chat-sub-tasks?chat_id=${chatId}`,
    {
      method: 'GET',
    },
  );
  return response;
};

export const requestV3UpdateChatSubTask = async (subTaskId: string, updatedAttrs: any) => {
  const response = await request(`${constants.API.baseUrl}v3.0/chat/update-chat-sub-task`, {
    method: 'POST',
    data: {
      chat_sub_task_id: subTaskId,
      updated_chat_sub_task_attrs: updatedAttrs,
    },
  });
  return response;
};

export const requestV3ToolCallBack = async (subTaskId: string, callbackData: any) => {
  const response = await request(
    `${constants.API.baseUrl}v3.0/chat/callback-chat-sub-task?chat_sub_task_id=${subTaskId}`,
    {
      method: 'POST',
      data: callbackData,
    },
  );
  return response;
};
