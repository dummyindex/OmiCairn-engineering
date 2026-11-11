export const NodeType = {
  DATA_NODE: 'data node',
  DATA_NODE_V2: 'data node v2',
  COMPUTATION_NODE: 'computation node',
  REPORT_NODE: 'report node',
  COMPUTATION_NODE_V2: 'computation node v2',
  NOTEBOOK_NODE: 'notebook node',
  CLAUDE_CODE_NODE: 'claude code node',
};

export const NodeState = {
  ORIGINAL: 'original',
  PENDING: 'pending',
  CANCELLED: 'cancelled',
  RUNNING: 'running',
  FINISHED: 'finished',
  FAILED: 'failed',
  DEBUGGING: 'debugging',
  GENERATING: 'generating',
  BEAUTIFYING: 'beautifying',
};

export const NodeListFetchMode = {
  ANALYSIS: 'analysis',
  IDX: 'idx',
};
