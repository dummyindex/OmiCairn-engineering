export interface UserRelation {
  analysisId: string | number;
  id: number;
  permission: string;
  relation: string;
  userId: string | number;
}

export type UserRelationList = UserRelation[];
