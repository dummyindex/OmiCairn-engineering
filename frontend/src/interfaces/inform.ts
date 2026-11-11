export enum InformCate {
  Notice = 'notice',
  Announcement = 'announcement',
}

export type Notice = {
  id: number;
  senderId: number;
  receiverId: number;
  type: string;
  createdTime: string;
  payload: string;
};

export type ExpandComputationEndNotice = {
  id: number;
  senderId: number;
  receiverId: number;
  type: string;
  createdTime: string;
  payload: {
    computation_id: number;
    node_id: number;
    success: string;
    error_description: string;
  };
};

export type Announcement = {
  id: number;
  content: string;
  createdTime: string;
};

export type ExpandAnnouncement = {
  id: number;
  content: {
    title: string;
    content: string;
  };
  createdTime: string;
};

// Enum definition
export enum InformType {
  AnalysisCollaborationInvitation = 'analysis_collaboration_invitation',
  ComputationEndNotice = 'computation_end_notice',
  InformationCompletionNotice = 'information_completion_notice',
}
