export interface FunctionBlock {
  id: number | string;
  name: string;
  type: string;
  groupId: number;
  ownerId: number;
  currentVersionId: number;
  createdTime: string;
}

export interface FunctionBlockVersion {
  id: number | string;
  name: string;
  functionBlockId: number;
  args: object | string | null;
  tag: string | null;
  documentUrl: string | null;
  description: string | null;
  source: string | null;
  plotOnly: boolean;
  runtimeVersion: string;
  createdTime: string;
  state: string;
  programLanguage: string;
  errorMessage: string | null;
}
