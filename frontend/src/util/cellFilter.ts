import type { DataCol } from '@/interfaces/col';
import { IndiciesBinarySearcher } from './indiciesBinarySearcher';
// import { DataCol } from "@/interfaces/col";
import { compareRange } from './rangeTool';
import { summaryObsCategory } from './summary';
import { getUuid } from './common';

export const getFilterKey = (
  field: string,
  isGeneSetSummary: boolean,
  isTopGeneSetSummary: boolean,
  isObs: boolean,
) => {
  if (isGeneSetSummary) {
    return `geneset_${field}`;
  }
  if (isTopGeneSetSummary) {
    return `top-geneset_${field}`;
  }
  if (isObs) {
    return `obs-continous_${field}`;
  }
  return `gene_${field}`;
};

class CellFilter {
  versionUuid: string = getUuid();
  continuousColValueRangeMap: Map<string, [number, number]> = new Map();
  continuousColMap: Map<string, DataCol> = new Map();
  category2Cluster2IndiciesMap: Map<string, Map<string, number[]>> = new Map();
  // category2ColMap: Map<string, DataCol> = new Map();
  queryTable: number[] | null = null;
  cellNumber: number | null = null;
  basicNumber: number = 0;

  constructor() {
    this.continuousColValueRangeMap = new Map();
    this.category2Cluster2IndiciesMap = new Map();
    this.queryTable = null;
    this.cellNumber = 0;
    this.basicNumber = 0;
  }

  reset(cellNumber?: number) {
    this.continuousColValueRangeMap = new Map();
    this.continuousColMap = new Map();
    this.category2Cluster2IndiciesMap = new Map();
    this.cellNumber = cellNumber || 0;
    this.basicNumber = 0;
    if (cellNumber === null || cellNumber === undefined) {
      this.queryTable = null;
    } else {
      this.queryTable = new Array(cellNumber).fill(0);
    }
  }

  copy(
    continuousColValueRangeMap,
    continuousColMap,
    category2Cluster2IndiciesMap,
    // cellNumber,
    basicNumber,
    queryTable,
  ) {
    this.continuousColValueRangeMap = continuousColValueRangeMap;
    this.continuousColMap = continuousColMap;

    this.category2Cluster2IndiciesMap = category2Cluster2IndiciesMap;
    // this.cellNumber = cellNumber;
    this.basicNumber = basicNumber;
    this.queryTable = queryTable;
  }

  public getCategoryFilterKeyList() {
    return Array.from(this.category2Cluster2IndiciesMap.keys());
  }

  public getContinuousFilterKeyList() {
    return Array.from(this.continuousColValueRangeMap.keys());
  }

  public upgradeVersionUuid() {
    this.versionUuid = getUuid();
  }

  public getVersionUuid() {
    return this.versionUuid;
  }

  public getEnable() {
    return this.basicNumber > 0;
  }

  // continuous filter related
  public setContinuousFilterCondition(
    key: string,
    dataCol: DataCol,
    newValueRange: [number, number],
  ) {
    const indiciesBinarySearcher = new IndiciesBinarySearcher(dataCol);

    const sortedCol = indiciesBinarySearcher.getSortedCol();

    if (this.continuousColValueRangeMap.has(key)) {
      const oldValueRange = this.continuousColValueRangeMap.get(key);
      if (!oldValueRange) {
        throw new Error('oldValueRange is null');
      }
      const { add: addedRanges, remove: removedRanges } = compareRange(
        oldValueRange,
        newValueRange,
      );

      for (const range of addedRanges) {
        const indiciesRange = indiciesBinarySearcher.searchIndiciesRange(range);
        for (let i = indiciesRange[0]; i <= indiciesRange[1]; i++) {
          this.queryTable![sortedCol.at(i).index] += 1;
        }
      }
      for (const range of removedRanges) {
        const indiciesRange = indiciesBinarySearcher.searchIndiciesRange(range);
        for (let i = indiciesRange[0]; i <= indiciesRange[1]; i++) {
          this.queryTable![sortedCol.at(i).index] -= 1;
        }
      }
      this.continuousColValueRangeMap.set(key, newValueRange);
    } else {
      // Enable filtering
      this.basicNumber += 1;
      const indiciesRange = indiciesBinarySearcher.searchIndiciesRange(newValueRange);

      for (let i = indiciesRange[0]; i <= indiciesRange[1]; i++) {
        this.queryTable![sortedCol.at(i).index] += 1;
      }
      this.continuousColValueRangeMap.set(key, newValueRange);
    }
    this.continuousColMap.set(key, dataCol);
  }

  public removeContinuousFilterCondition(key: string) {
    const oldValueRange = this.continuousColValueRangeMap.get(key);
    const dataCol = this.continuousColMap.get(key);
    if (!oldValueRange) {
      throw new Error('oldValueRange is null');
    }
    if (!dataCol) {
      throw new Error('no this data col');
    }
    const indiciesBinarySearcher = new IndiciesBinarySearcher(dataCol);
    const sortedCol = indiciesBinarySearcher.getSortedCol();
    const indiciesRange = indiciesBinarySearcher.searchIndiciesRange(oldValueRange);
    for (let i = indiciesRange[0]; i <= indiciesRange[1]; i++) {
      this.queryTable![sortedCol.at(i).index] -= 1;
    }
    this.continuousColValueRangeMap.delete(key);
    this.continuousColMap.delete(key);

    this.basicNumber -= 1;
  }

  public removeAllContinuousFilterConditions() {
    const keys = new Array(...this.continuousColMap.keys());
    for (const key of keys) {
      this.removeContinuousFilterCondition(key);
    }
  }
  public removeContinuousFilterConditionsByKey(key) {
    if (this.continuousColMap.has(key)) {
      this.removeContinuousFilterCondition(key);
    }
  }

  // category filter related
  public maskByCategory(key: string, dataCol: DataCol) {
    const categorySummary = summaryObsCategory(dataCol);
    const { cluster2IndexList } = categorySummary;
    this.category2Cluster2IndiciesMap.set(key, new Map(cluster2IndexList));
    for (let i = 0; i < this.queryTable!.length; i++) {
      this.queryTable![i] -= 1;
    }
  }

  public unmaskByCategory(key: string) {
    const cluster2IndiciesMap = this.category2Cluster2IndiciesMap.get(key);
    if (!cluster2IndiciesMap) {
      throw new Error('cluster2IndiciesMap is null');
    }
    for (const indicies of cluster2IndiciesMap.values()) {
      for (const index of indicies) {
        this.queryTable![index] += 1;
      }
    }
    this.category2Cluster2IndiciesMap.delete(key);
  }

  public unmaskAllCategories() {
    const categoryKeys = Array.from(this.category2Cluster2IndiciesMap.keys());
    for (const key of categoryKeys) {
      this.unmaskByCategory(key);
    }
  }

  public queryByCategory(key: string) {
    return !this.category2Cluster2IndiciesMap.has(key);
  }

  public maskByCluster(key: string, cluster: string, dataCol: DataCol) {
    const categorySummary = summaryObsCategory(dataCol);
    const { cluster2IndexList } = categorySummary;
    const indicies = cluster2IndexList.get(cluster);
    if (
      this.category2Cluster2IndiciesMap.has(key) &&
      !!this.category2Cluster2IndiciesMap.get(key)
    ) {
      const cluster2IndiciesMap = this.category2Cluster2IndiciesMap.get(key);
      if (cluster2IndiciesMap?.has(cluster)) {
        throw new Error('cluster was already masked');
      } else {
        cluster2IndiciesMap!.set(cluster, indicies!);
        for (const index of indicies!) {
          this.queryTable![index] -= 1;
        }
      }
    } else {
      this.category2Cluster2IndiciesMap.set(key, new Map([[cluster, indicies!]]));
      for (const index of indicies!) {
        this.queryTable![index] -= 1;
      }
    }
  }

  public unmaskByCluster(key: string, cluster: string) {
    const cluster2IndiciesMap = this.category2Cluster2IndiciesMap.get(key);
    if (!cluster2IndiciesMap) {
      throw new Error('cluster2IndiciesMap is null');
    }
    const indicies = cluster2IndiciesMap.get(cluster);
    if (!indicies) {
      throw new Error('indicies is null');
    }
    for (const index of indicies) {
      this.queryTable![index] += 1;
    }
    cluster2IndiciesMap.delete(cluster);
    if (cluster2IndiciesMap.size === 0) {
      this.category2Cluster2IndiciesMap.delete(key);
    }
  }

  public queryByCluster(key: string, cluster: string) {
    const cluster2IndiciesMap = this.category2Cluster2IndiciesMap.get(key);
    if (!cluster2IndiciesMap) {
      return true;
    }
    return !cluster2IndiciesMap.has(cluster);
  }

  public queryByIndex(index: number) {
    if (this.queryTable === null) {
      throw new Error('queryTable is null');
    }
    return this.queryTable[index] === this.basicNumber;
  }

  public getQueryTable() {
    return this.queryTable;
  }

  public getBasicNumber() {
    return this.basicNumber;
  }
}

export const cellSelectorFilter = new CellFilter();
