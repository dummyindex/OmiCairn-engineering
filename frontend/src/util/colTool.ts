import { memoize } from '@/util/fnTool';
import { DataCol } from '@/interfaces/col';

export const searchStringColPrecisely = memoize(
  (col: DataCol, searchList: string[]) => {
    const value2Index = new Map();
    for (let i = 0; i < searchList.length; i++) {
      value2Index.set(searchList[i], null);
    }
    for (let i = 0; i < col.getLength(); i++) {
      const colValue = col.at(i);
      if (value2Index.has(colValue)) {
        value2Index.set(colValue, i);
      }
    }
    return searchList.map((value) => {
      return value2Index.get(value);
    });
  },
  (col: DataCol, searchList: string[]) => {
    return `${col.getColId()}:${searchList.join(',')}`;
  },
  30,
);

export const meanCols: (cols: DataCol[]) => DataCol = memoize(
  (cols: DataCol[]) => {
    if (cols.length === 0) {
      return new DataCol();
    }
    const meanCol = new DataCol(cols[0].getLength());
    for (let i = 0; i < cols[0].getLength(); i++) {
      let sum = 0;
      for (let j = 0; j < cols.length; j++) {
        sum += cols[j].at(i);
      }
      meanCol.set(i, sum / cols.length);
    }
    return meanCol;
  },
  (cols: DataCol[]) => {
    if (cols.length === 0) {
      return '';
    }
    const colIds = cols.map((col) => col.getColId());
    const sortedColIds = colIds.sort();
    return sortedColIds.join(',');
  },
  20,
);

export const combinedIndexAndValueCol: (col: DataCol) => DataCol = memoize(
  (col: DataCol) => {
    const combinedCol = col.map((value, index) => {
      return { value, index };
    });
    return combinedCol;
  },
  (col: DataCol) => {
    return col.getColId();
  },
  30,
);

export const sortCol: (
  col: DataCol,
  cacheKey: string,
  compareFn?: (a: any, b: any) => number,
) => DataCol = memoize(
  (col: DataCol, _: any, compareFn?: (a: any, b: any) => number) => {
    const newCol = DataCol.from(col.getElements());
    return newCol.sort(compareFn);
  },
  (col: DataCol, cacheKey: string) => {
    return col.getColId() + cacheKey;
  },
  30,
);
