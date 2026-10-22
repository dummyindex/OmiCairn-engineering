import * as constants from '@/constants/index';
import { request } from 'umi';

// Base interaction type
export interface DynamicGenerationInteraction {
  id: string; // Format: dgs_{session_id} or bfs_{session_id}
  type: 'dynamic_generation' | 'bug_fixer';
  session_id: number;
  interaction_source: 'next_fb_generation' | 'computation_retry_bug_fixer';
  // dynamic_generation-specific fields
  source_node_id?: number;
  dynamic_generation_id?: number;
  // bug_fixer-specific fields
  node_id?: number;
  retry_process_id?: number;
  // Common fields
  is_valid: boolean;
  errors?: string;
  start_time?: number; // Timestamp in milliseconds
  end_time?: number; // Timestamp in milliseconds
  created_at?: number; // Timestamp in milliseconds
  session_type?: string;
}

// Branch info
export interface DynamicGenerationBranch {
  branch_id: number;
  end_node_id: number;
  state: string;
  created_time?: number;
  updated_time?: number;
  interactions: DynamicGenerationInteraction[];
  total_interactions: number;
  nodes_in_branch: number[];
}

// Mixed-mode response
export interface DynamicGenerationInteractionsResponse {
  code: number;
  data: {
    generation_id: number;
    previous_node_id: number;
    state: string;
    branches: DynamicGenerationBranch[];
    total_branches: number;
    last_updated: number;
  };
}

// Unified request function
export const requestDynamicGenerationInteractions = async (
  generationId: number,
): Promise<DynamicGenerationInteractionsResponse> => {
  const result = await request(
    `${constants.API.computationServerUrl}dynamic-generation-llm-monitor/interactions`,
    {
      method: 'GET',
      params: {
        generation_id: generationId,
      },
      skipErrorHandler: true,
    },
  );
  return result;
};

// Response type of the interaction-detail API
export interface InteractionDetailsResponse {
  code: number;
  data: {
    interaction_type: string;
    session_id: number;
    input: any;
    output: any;
    files_found: string[];
  };
}

// Request function to get interaction details
// TODO: clean up, together with the API
export const requestInteractionDetails = async (
  interactionType: string,
  sessionId: number,
  dynamicGenerationId?: number,
  retryProcessId?: number,
  nodeId?: number,
): Promise<InteractionDetailsResponse> => {
  const params: any = {
    interaction_type: interactionType,
    session_id: sessionId,
  };

  if (dynamicGenerationId !== undefined) {
    params.dynamic_generation_id = dynamicGenerationId;
  }
  if (retryProcessId !== undefined) {
    params.retry_process_id = retryProcessId;
  }
  if (nodeId !== undefined) {
    params.node_id = nodeId;
  }

  const result = await request(
    `${constants.API.computationServerUrl}dynamic-generation-llm-monitor/interaction-details`,
    {
      method: 'GET',
      params,
      skipErrorHandler: true,
    },
  );
  return result;
};
