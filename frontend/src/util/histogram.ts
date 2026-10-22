// Adapted from cellxgene (https://github.com/chanzuckerberg/cellxgene),
// Copyright (c) Chan Zuckerberg Initiative. MIT License; see THIRD_PARTY_NOTICES.md.
import type { DataCol } from '@/interfaces/col';
import { memoize } from './fnTool';

function isTypedArray(x) {
  return ArrayBuffer.isView(x) && Object.prototype.toString.call(x) !== '[object DataView]';
}

function _histogramContinuous(column: DataCol, bins, min, max) {
  const valBins = new Array(bins).fill(0);
  if (!column) {
    return valBins;
  }
  const binWidth = (max - min) / bins;
  for (let r = 0, len = column.getLength(); r < len; r += 1) {
    const val = column.at(r);
    if (val <= max && val >= min) {
      // ensure test excludes NaN values
      const valBin = Math.min(Math.floor((val - min) / binWidth), bins - 1);
      valBins[valBin] += 1;
    }
  }
  return valBins;
}

function _histogramContinuousBy(column: DataCol, bins, min, max, by) {
  const byMap = new Map();
  if (!column || !by) {
    return byMap;
  }
  const binWidth = (max - min) / bins;
  const byArray = by.asArray();
  for (let r = 0, len = column.getLength(); r < len; r += 1) {
    const byBin = byArray[r];
    let valBins = byMap.get(byBin);
    if (valBins === undefined) {
      valBins = new Array(bins).fill(0);
      byMap.set(byBin, valBins);
    }
    const val = column.at(r);
    if (val <= max && val >= min) {
      // ensure test excludes NaN values
      const valBin = Math.min(Math.floor((val - min) / binWidth), bins - 1);
      valBins[valBin] += 1;
    }
  }
  return byMap;
}

// function _histogramCategorical(column: DataCol) {
//     const valMap = new Map();
//     if (!column) {
//         return valMap;
//     }
//     for (let r = 0, len = column.getLength(); r < len; r += 1) {
//         const valBin = column.at(r);
//         let curCount = valMap.get(valBin);
//         if (curCount === undefined) {
//             curCount = 0;
//         }
//         valMap.set(valBin, curCount + 1);
//     }
//     return valMap;
// }

// function _histogramCategoricalBy(column: DataCol, by) {
//     const byMap = new Map();
//     if (!column || !by) {
//         return byMap;
//     }
//     const byArray = by.asArray();
//     for (let r = 0, len = column.getLength(); r < len; r += 1) {
//         const byBin = byArray.at(r);
//         let valMap = byMap.get(byBin);
//         if (valMap === undefined) {
//             valMap = new Map();
//             byMap.set(byBin, valMap);
//         }
//         const valBin = column.at(r);
//         let curCount = valMap.get(valBin);
//         if (curCount === undefined) {
//             curCount = 0;
//         }
//         valMap.set(valBin, curCount + 1);
//     }
//     return byMap;
// }

export const histogramContinuous = memoize(
  (column: DataCol, bins = 40, domain = [0, 1], by) => {
    if (by && isTypedArray(by)) {
      throw new Error('Group by column must be categorical');
    }
    const [min, max] = domain;
    return by
      ? _histogramContinuousBy(column, bins, min, max, by)
      : _histogramContinuous(column, bins, min, max);
  },
  (column: DataCol, bins = 40, domain = [0, 1], by) => {
    const key = `${column.getColId()}-${bins}-${domain}-${by || 'no-by'}`;
    // console.log(key);
    return key;
  },
  100,
);
