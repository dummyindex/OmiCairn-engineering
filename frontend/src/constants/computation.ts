export const ComputationState = {
  PENDING: 'pending',
  QUEUING: 'queuing',
  RUNNING: 'running',
  FINISHED: 'finished',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
};

export const ComputationStateColorMap = {
  [ComputationState.PENDING]: '#939393',
  [ComputationState.QUEUING]: '#939393',
  [ComputationState.RUNNING]: '#939393',
  [ComputationState.FINISHED]: '#4D9A17',
  [ComputationState.FAILED]: '#C74242',
  [ComputationState.CANCELLED]: '#fff',
};

export const SystemEnv = {
  SERVER_LOCAL: 'server-local',
  AWS_BATCH: 'aws-batch',
};
