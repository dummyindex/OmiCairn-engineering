import { getUuid } from '@/util/common';

export class SelectionPolygon {
  private pointArray: [number, number][];
  private uniqueKey: string;
  constructor(pointArray: [number, number][] = []) {
    if (pointArray.length < 3) {
      this.uniqueKey = 'empty selection range';
    } else {
      this.uniqueKey = getUuid();
    }
    this.pointArray = pointArray;
  }

  public getRangeSize() {
    return this.pointArray.length;
  }

  public getUniqueKey() {
    return this.uniqueKey;
  }

  public getPointArray() {
    return this.pointArray;
  }
}
