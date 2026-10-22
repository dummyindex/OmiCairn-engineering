import type { DataCol } from '@/interfaces/col';
import { combinedIndexAndValueCol, sortCol } from './colTool';

export class IndiciesBinarySearcher {
  sortedCol: DataCol;
  indicies: [number, number][] = [];
  min: number = 0;
  max: number = 0;
  constructor(dataCol: DataCol) {
    const combinedCol = combinedIndexAndValueCol(dataCol);
    const sortedCol = sortCol(combinedCol, 'sortByValueAsc', (a, b) => {
      return a.value - b.value;
    });
    this.sortedCol = sortedCol;
  }

  getSortedCol() {
    return this.sortedCol;
  }

  // Binary search
  binarySearch(target: number) {
    let left = 0;
    let right = this.sortedCol.getLength() - 1;

    while (left <= right) {
      const mid = Math.floor((left + right) / 2);
      if (this.sortedCol.at(mid).value === target) {
        return mid;
      } else if (this.sortedCol.at(mid).value < target) {
        left = mid + 1;
      } else {
        right = mid - 1;
      }
    }
    // a negative return value means not found and encodes the insertion position
    return ~left;
  }

  search(range: [number, number]): number[] {
    const [start, end] = range;
    const result: number[] = [];

    if (this.sortedCol.getLength() === 0 || start > end) {
      return result; // return an empty array because the input is invalid or the array is empty
    }

    let startIndex = this.binarySearch(start);
    let endIndex = this.binarySearch(end);

    // handle start/end values that are not in the array
    if (startIndex < 0) {
      startIndex = ~startIndex;
    }
    if (endIndex < 0) {
      endIndex = ~endIndex - 1;
    }

    for (let i = startIndex; i <= endIndex; i++) {
      result.push(this.sortedCol.at(i).index);
    }

    return result;
  }

  searchIndiciesRange(range: [number, number]): [number, number] {
    const [start, end] = range;

    if (this.sortedCol.getLength() === 0 || start > end) {
      return [0, 0]; // return an empty array because the input is invalid or the array is empty
    }

    let startIndex = this.binarySearch(start);

    while (this.sortedCol.at(startIndex).value === start) {
      startIndex--;
    }
    let endIndex = this.binarySearch(end);

    // handle start/end values that are not in the array
    if (startIndex < 0) {
      startIndex = ~startIndex;
    }
    if (endIndex < 0) {
      endIndex = ~endIndex - 1;
    }

    return [startIndex, endIndex];
  }
}
