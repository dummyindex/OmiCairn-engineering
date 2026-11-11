import { getUuid } from '@/util/common';

export class DataCol {
  static from(source: any) {
    const s = source;
    if (Array.isArray(s)) {
      return new DataCol([...s]);
    } else {
      return new DataCol(Array.from(s));
    }
  }

  private col_id: string;
  private elements: any[];
  constructor(arrayLength: number);
  constructor(...items: any[]);
  constructor(...initialParams: any[]) {
    if (initialParams.length === 0) {
      this.elements = [];
    } else if (initialParams.length === 1) {
      if (typeof initialParams[0] === 'number') {
        this.elements = new Array(initialParams[0]).fill(0);
      } else if (initialParams[0] instanceof Array) {
        this.elements = initialParams[0];
      } else if (initialParams[0] instanceof Set) {
        this.elements = Array.from(initialParams[0]);
      } else {
        throw new Error('DataCol constructor error: invalid initial params');
      }
    } else {
      this.elements = new Array(...initialParams);
    }
    this.col_id = getUuid();
  }
  public fromElementsAndId(elements: any[], col_id: string) {
    const dataColInstance = new DataCol(elements);
    dataColInstance.col_id = col_id; // Set col_id
    return dataColInstance;
  }

  public at(index: number) {
    return this.elements.at(index);
  }

  public set(index: number, value: any) {
    this.elements[index] = value;
  }

  public getColId() {
    return this.col_id;
  }

  public getElements() {
    return this.elements;
  }

  public getLength() {
    return this.elements.length;
  }

  public map(callbackfn: (value: any, index: number, array: any[]) => any, thisArg?: any) {
    const newArray = this.elements.map(callbackfn, thisArg);
    return new DataCol(newArray);
  }

  public filter(callbackfn: (value: any, index: number, array: any[]) => any, thisArg?: any) {
    const newArray = this.elements.filter(callbackfn, thisArg);
    return new DataCol(newArray);
  }

  public slice(start?: number, end?: number) {
    const newArray = this.elements.slice(start, end);
    return new DataCol(newArray);
  }

  public concat(arrayLike: any[] | DataCol) {
    if (arrayLike instanceof DataCol) {
      const newArray = this.elements.concat(arrayLike.getElements());
      return new DataCol(newArray);
    } else {
      const newArray = this.elements.concat(arrayLike);
      return new DataCol(newArray);
    }
  }

  public splice(start: number, deleteCount: number, ...items: any[]) {
    const replacedPart = this.elements.splice(start, deleteCount, ...items);
    return new DataCol(replacedPart);
  }

  public reverse() {
    this.elements.reverse();
    return this;
  }

  public sort(compareFn?: (a: any, b: any) => number) {
    this.elements.sort(compareFn);
    return this;
  }

  public reduce(
    reduceFn: (previousValue: any, currentValue: any, index: number) => any,
    originalValue: any,
  ) {
    return this.elements.reduce(reduceFn, originalValue);
  }

  public forEach(travelFn: (value: any, index: number) => any) {
    this.elements.forEach(travelFn);
  }
}
