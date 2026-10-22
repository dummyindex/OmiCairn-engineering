import type { DataCol } from '@/interfaces/col';
import { memoize } from './fnTool';

interface CategorySummary {
  clusters: string[];
  cluster2IndexList: Map<string, number[]>;
  cluster2Count: Map<string, number>;
}

const _summaryObsCategory = (obsCol: DataCol) => {
  const cluster2IndexList = new Map<string, number[]>();
  const cluster2Count = new Map<string, number>();
  const clusters: Set<string> = new Set();
  for (let i = 0; i < obsCol.getLength(); i++) {
    const value = obsCol.at(i);
    if (cluster2IndexList.has(value)) {
      cluster2IndexList.get(value)!.push(i);
      cluster2Count.set(value, cluster2Count.get(value)! + 1);
    } else {
      cluster2IndexList.set(value, [i]);
      cluster2Count.set(value, 1);
      clusters.add(value);
    }
  }
  return {
    clusters: Array.from(clusters),
    cluster2IndexList,
    cluster2Count,
  };
};

export const summaryObsCategory: (col: DataCol) => CategorySummary = memoize(
  _summaryObsCategory,
  (obsCol: DataCol) => {
    return obsCol.getColId();
  },
  100,
);

interface ContinuousSummary {
  min: number;
  max: number;
  mean: number;
  sum: number;
}

const _summaryContinuousCol = (col: DataCol) => {
  const summary: any = {};
  let min = Infinity;
  let max = -Infinity;
  let sum = 0;

  for (let i = 0; i < col.getLength(); i++) {
    const value = col.at(i);
    if (value < min) {
      min = value;
    }
    if (value > max) {
      max = value;
    }
    sum += value;
  }

  summary.min = min;
  summary.max = max;
  summary.mean = sum / col.getLength();
  summary.sum = sum;

  return summary;
};

export const summaryContinuousCol: (col: DataCol) => ContinuousSummary = memoize(
  _summaryContinuousCol,
  (col: DataCol) => {
    return col.getColId();
  },
  50,
);

export const summaryCellTypeProportionsOfEachCluster: (
  whichHasCluster: DataCol,
  whichHasCellType: DataCol,
) => Map<string, Map<string, number>> = memoize(
  (whichHasCluster: DataCol, whichHasCellType: DataCol) => {
    const whichHasCellTypeSummary = summaryObsCategory(whichHasCellType);
    const zeroCellTypeMapTemplate = whichHasCellTypeSummary.clusters.reduce(
      (preMap, clusterItem) => {
        preMap.set(clusterItem, 0);
        return preMap;
      },
      new Map(),
    );
    const clusterMap = whichHasCluster.reduce((map, cluster, index) => {
      const cellType = whichHasCellType.at(index);
      if (map.has(cluster)) {
        const cellTypeMap = map.get(cluster)!;
        if (cellTypeMap.has(cellType)) {
          cellTypeMap.set(cellType, cellTypeMap.get(cellType)! + 1);
        } else {
          cellTypeMap.set(cellType, 1);
        }
        map.set(cluster, cellTypeMap);
      } else {
        const cellTypeMap = new Map(zeroCellTypeMapTemplate);
        cellTypeMap.set(cellType, 1);
        map.set(cluster, cellTypeMap);
      }
      return map;
    }, new Map());

    const whichHasClusterSummary = summaryObsCategory(whichHasCluster);
    for (const cluster of clusterMap.keys()) {
      const cellTypeMap = clusterMap.get(cluster);
      for (const cellType of cellTypeMap.keys()) {
        const count = cellTypeMap.get(cellType);
        cellTypeMap.set(cellType, count / whichHasClusterSummary.cluster2Count.get(cluster));
      }
    }

    return clusterMap;
  },
  (whichHasCluster: DataCol, whichHasCellType: DataCol) => {
    return `${whichHasCluster.getColId()}:${whichHasCellType.getColId()}`;
  },
  10,
);
