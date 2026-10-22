export type CollaborationInvitation = {
  id: number;
  inviterId: number;
  inviteeId: number;
  otype: string;
  oid: number;
  permission: string;
  createdTime: string;
  oname: string;
  message: string;
  status: InvitationStatus;
  inviterName: string;
};

export enum InvitationStatus {
  Pending = 'pending',
  Accepted = 'accepted',
  Rejected = 'rejected',
  Cancelled = 'cancelled',
}
