import { DataCol } from '@/interfaces/col';

import { memoize } from './fnTool';
import { summaryContinuousCol } from './summary';

export const normalizeContinuousCol = memoize(
  (col: DataCol) => {
    const summary = summaryContinuousCol(col);
    const normalizedCol = new DataCol(col.getLength());
    const range = summary.max - summary.min;
    for (let i = 0; i < col.getLength(); i++) {
      if (range === 0) {
        normalizedCol.set(i, 0);
        continue;
      }
      normalizedCol.set(i, ((Math.floor(col.at(i) - summary.min) / range) * 10000) / 10000);
    }
    return normalizedCol;
  },
  (col: DataCol) => {
    return col.getColId();
  },
  50,
);
