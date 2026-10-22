import { SpecialUserId, Permission } from '@/constants/userRelation';
import type { UserRelationList, UserRelation } from '@/interfaces/userRelation';

// priority ranking: ALL < ... < USER
const getPriority = (userId: string | number) => {
  switch (userId + '') {
    case SpecialUserId.ALL + '':
      return 0;
    default:
      return 1000;
  }
};

export class UserRelationTool {
  currentUserId: string;
  userRelationList: UserRelationList;
  published: boolean;
  readable: boolean;
  writable: boolean;
  currentUserRelation: UserRelation | null;

  constructor(currentUserId: string | number, userRelationList: UserRelationList) {
    this.currentUserId = currentUserId + '';
    this.userRelationList = [...userRelationList];
    this.published = false;
    this.readable = false;
    this.writable = false;
    this.currentUserRelation = null;
    this._teaseUserRelation();
  }

  _teaseUserRelation() {
    if (this.userRelationList.length === 0) {
      return;
    }
    this.userRelationList.sort((userRelation1: UserRelation, userRelation2: UserRelation) => {
      return getPriority(userRelation2.userId) - getPriority(userRelation1.userId);
    });
    this.currentUserRelation = this.userRelationList[0];
    this.published =
      this.userRelationList.findIndex(
        (userRelation: UserRelation) => userRelation.userId === SpecialUserId.ALL,
      ) !== -1;

    // Handle public separately
    if (
      this.currentUserId !== this.currentUserRelation.userId + '' &&
      this.currentUserRelation.userId === SpecialUserId.PUBLIC
    ) {
      this.readable = true;
      return;
    }
    const permission = this.currentUserRelation.permission;
    this.readable = !!permission && Permission[permission] >= Permission.read;
    this.writable = !!permission && Permission[permission] >= Permission.write;
  }

  isPublished() {
    return this.published;
  }

  isReadable() {
    return this.readable;
  }

  isWritable() {
    return this.writable;
  }
}
