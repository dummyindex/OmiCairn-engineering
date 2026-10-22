import { request } from 'umi';
import { API } from '@/constants/index';

export interface ChatSession {
  id: string;
  analysisId: string | null;
  title: string;
  createdTime: number;
  updatedTime: number;
  messageCount: number;
  isActive: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  files?: any[];
  contextNodes?: any;
  contextType?: 'analysis' | 'pipeline' | 'node' | 'multinodes';
  model?: string;
}

export interface CreateSessionRequest {
  contextType?: 'analysis' | 'pipeline' | 'node' | 'multinodes';
  title?: string;
  model?: string;
}

export interface SendMessageRequest {
  content: string;
  files?: any[];
  model?: string;
  contextType?: 'analysis' | 'pipeline' | 'node' | 'multinodes';
  nodeId?: string;
  nodeIds?: string[];
  dataNodeId?: string;
}

class ChatbotService {
  // Create a new chat session
  async createSession(analysisId: string | null, data: CreateSessionRequest): Promise<ChatSession> {
    return request(`${API.baseUrl}api/v1/analysis/${analysisId}/chat/sessions`, {
      method: 'POST',
      data,
    });
  }

  // Get chat session history for an analysis
  async getSessionHistory(analysisId: string | null): Promise<ChatSession[]> {
    return request(`${API.baseUrl}api/v1/analysis/${analysisId}/chat/sessions`, {
      method: 'GET',
    });
  }

  // Delete a chat session
  async deleteSession(sessionId: string): Promise<{ message: string }> {
    return request(`${API.baseUrl}api/v1/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // Get messages for a session
  async getMessages(sessionId: string): Promise<ChatMessage[]> {
    return request(`${API.baseUrl}api/v1/chat/sessions/${sessionId}/messages`, {
      method: 'GET',
    });
  }

  // Send a message
  async sendMessage(sessionId: string, data: SendMessageRequest): Promise<ChatMessage> {
    return request(`${API.baseUrl}api/v1/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      data,
    });
  }
}

export default new ChatbotService();
