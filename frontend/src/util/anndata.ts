import { Component } from '@/constants/visual';
import type {
  DataStructure,
  Layers,
  Matrix,
  ObsDataframe,
  OBSM,
  OBSP,
  UNS,
  VarDataframe,
  VARM,
  VARP,
} from '@/interfaces/anndata';
import { DataCol } from '@/interfaces/col';
import {
  requestAddVisualData,
  requestDeleteVisualData,
  requestEditVisualData,
  requestRenameVisualData,
  requestVisualData,
} from '@/request/visual';
import { searchStringColPrecisely } from './colTool';
import { DataOutdatedError } from '@/errors/dataOutdated';
import { promiseLockFactory } from './promiseLock';
import { requestGetDataStructure } from '@/request/attachedData';

export class Anndata {
  dataId: string;
  dataStructure: DataStructure | null;
  X: Matrix;
  obsNames: DataCol | null;
  varNames: DataCol | null;
  obsDataframe: ObsDataframe;
  varDataframe: VarDataframe;
  layers: Layers;
  obsm: OBSM;
  varm: VARM;
  obsp: OBSP;
  varp: VARP;
  uns: UNS;
  constructor() {
    this.dataId = '' as string;
    this.dataStructure = null as DataStructure | null;
    this.X = [] as Matrix;
    this.obsNames = null as DataCol | null;
    this.varNames = null as DataCol | null;
    this.obsDataframe = {} as ObsDataframe;
    this.varDataframe = {} as VarDataframe;
    this.layers = {} as Layers;
    this.obsm = {} as OBSM;
    this.varm = {} as VARM;
    this.obsp = {} as OBSP;
    this.varp = {} as VARP;
    this.uns = {} as UNS;
  }

  clearAll() {
    this.dataId = '' as string;
    this.dataStructure = null as DataStructure | null;
    this.X = [] as Matrix;
    this.obsNames = null as DataCol | null;
    this.varNames = null as DataCol | null;
    this.obsDataframe = {} as ObsDataframe;
    this.varDataframe = {} as VarDataframe;
    this.layers = {} as Layers;
    this.obsm = {} as OBSM;
    this.varm = {} as VARM;
    this.obsp = {} as OBSP;
    this.varp = {} as VARP;
    this.uns = {} as UNS;
  }

  setDataId(dataId: string) {
    this.clearAll();
    this.dataId = dataId;
  }

  getObsNameByIndex(index: number) {
    return this.obsNames ? this.obsNames[index] : null;
  }

  async _getStructure() {
    const _dataId = this.dataId;
    if (this.dataStructure) {
      return this.dataStructure;
    }
    const { data: newDataStructure } = await requestGetDataStructure(this.dataId);
    if (this.dataId !== _dataId) {
      return;
    }
    this.dataStructure = newDataStructure;
    return this.dataStructure;
  }

  async getStructure() {
    const lockKey = `anndata-${this.dataId}-data-structure`;
    const lock = promiseLockFactory.getLock(lockKey);
    await lock.acquire();
    try {
      return await this._getStructure();
    } finally {
      lock.release();
    }
  }

  async _getObsNames() {
    const _dataId = this.dataId;
    if (this.obsNames) {
      return this.obsNames;
    }
    const { data: newObsNames } = await requestVisualData(this.dataId, {
      component: Component.OBS_NAMES,
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    this.obsNames = new DataCol(newObsNames);
    return this.obsNames;
  }

  async getObsNames() {
    const lockKey = `anndata-${this.dataId}-obs-names`;
    const lock = promiseLockFactory.getLock(lockKey);
    await lock.acquire();
    try {
      return await this._getObsNames();
    } finally {
      lock.release();
    }
  }

  async _getVarNames() {
    const _dataId = this.dataId;
    if (this.varNames) {
      return this.varNames;
    }
    const { data: newVarNames } = await requestVisualData(this.dataId, {
      component: Component.VAR_NAMES,
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    this.varNames = new DataCol(newVarNames);
    return this.varNames;
  }

  async getVarNames() {
    const lockKey = `anndata-${this.dataId}-var-names`;
    const lock = promiseLockFactory.getLock(lockKey);
    await lock.acquire();
    try {
      return await this._getVarNames();
    } finally {
      lock.release();
    }
  }

  async getIndexByVarNameList(searchedList: string[]) {
    const varNames = await this.getVarNames();
    const result = searchStringColPrecisely(varNames, searchedList);
    return result;
  }

  async _getObsCol(key: string) {
    const _dataId = this.dataId;
    if (this.obsDataframe[key]) {
      return this.obsDataframe[key];
    }
    const { data: newObsCols } = await requestVisualData(this.dataId, {
      component: Component.OBS,
      keys: [key],
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    if (!newObsCols) {
      return null;
    }
    const [newObsCol] = newObsCols;
    if (!newObsCol) {
      return null;
    }
    this.obsDataframe[key] = new DataCol(newObsCol);
    return this.obsDataframe[key];
  }

  async getObsCol(key: string) {
    const lockKey = `anndata-${this.dataId}-obs-${key}`;
    const lock = promiseLockFactory.getLock(lockKey);
    await lock.acquire();
    try {
      return await this._getObsCol(key);
    } finally {
      lock.release();
    }
  }

  async _getXCols(colIndexes: number[]) {
    const _dataId = this.dataId;
    const lackColIndexes = colIndexes.filter((i: number) => {
      return !this.X[i];
    });
    if (lackColIndexes.length > 0) {
      const { data: partMatrix }: any = await requestVisualData(this.dataId, {
        component: Component.X,
        colIndexes: lackColIndexes,
      });
      if (_dataId !== this.dataId) {
        throw new DataOutdatedError('data outdated!');
      }
      lackColIndexes.forEach((lackColIndex: number, index: number) => {
        this.X[lackColIndex] = new DataCol(
          partMatrix.map((row: number[]) => {
            return row[index];
          }),
        );
      });
    }
    return colIndexes.map((index: number) => {
      return this.X[index];
    });
  }

  async getXCols(colIndexes: number[]) {
    const lockKey = `anndata-${this.dataId}-X-cols`;
    const lock = promiseLockFactory.getLock(lockKey);
    await lock.acquire();
    try {
      return await this._getXCols(colIndexes);
    } finally {
      lock.release();
    }
  }

  async getUns(keyPath: string[]) {
    const _dataId = this.dataId;
    if (!keyPath || keyPath.length === 0) {
      return null;
    }
    let ptr = this.uns;
    for (const key of keyPath.slice(0, -1)) {
      if (!ptr[key]) {
        ptr[key] = {};
      } else if (typeof ptr[key] !== 'object') {
        console.error('error key path');
        return null;
      }
      ptr = ptr[key];
    }
    const lastKey = keyPath[keyPath.length - 1];
    if (!ptr[lastKey]) {
      const { data } = await requestVisualData(this.dataId, {
        component: Component.UNS,
        key_path: keyPath,
      });
      if (_dataId !== this.dataId) {
        throw new DataOutdatedError('data outdated!');
      }
      ptr[lastKey] = data;
    }
    return ptr[lastKey];
  }

  async _getObsm(embeddingKey: string, colIndexes: number[]) {
    const _dataId = this.dataId;
    if (!this.obsm[embeddingKey]) {
      this.obsm[embeddingKey] = [];
    }

    const lackColIndexes = colIndexes.filter((i: number) => {
      return !this.obsm[embeddingKey][i];
    });
    // console.log('colIndexes', colIndexes);

    // console.log('this.obsm', this.obsm);

    // console.log('lackColIndexes', lackColIndexes);

    if (lackColIndexes.length > 0) {
      const { data: partMatrix }: any = await requestVisualData(this.dataId, {
        component: Component.OBSM,
        key: embeddingKey,
        colIndexes: lackColIndexes,
      });
      if (_dataId !== this.dataId) {
        throw new DataOutdatedError('data outdated!');
      }
      // console.log('-----------lackColIndexes', lackColIndexes);
      // console.log('-----------this.obsm', this.obsm);

      lackColIndexes.forEach((lackColIndex: number, index: number) => {
        this.obsm[embeddingKey][lackColIndex] = new DataCol(
          partMatrix.map((row: number[]) => {
            return row[index];
          }),
        );
      });
    }
    return colIndexes.map((i: number) => {
      return this.obsm[embeddingKey][i];
    });
  }

  async getObsm(embeddingKey: string, colIndexes: number[]) {
    const lockKey = `anndata-${this.dataId}-obsm-${embeddingKey}`;
    const lock = promiseLockFactory.getLock(lockKey);
    await lock.acquire();
    try {
      return await this._getObsm(embeddingKey, colIndexes);
    } finally {
      lock.release();
    }
  }

  async getCellset(cellsetName: string) {
    const _dataId = this.dataId;
    if (this.uns.customCellsets) {
      return this.uns.customCellsets;
    }
    const { data: newCellSets } = await requestVisualData(this.dataId, {
      component: Component.UNS,
      key_path: ['customCellsets'],
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    this.uns.customCellsets = newCellSets || {};
    return this.uns.customCellsets[cellsetName];
  }

  async getAnnotationset(annotationsetName: string) {
    const _dataId = this.dataId;
    if (this.uns.customAnnotationsets) {
      return this.uns.customAnnotationsets;
    }
    const { data: newAnnotationSets } = await requestVisualData(this.dataId, {
      component: Component.UNS,
      key_path: ['customAnnotationsets'],
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    this.uns.customAnnotationsets = newAnnotationSets || {};
    return this.uns.customAnnotationsets[annotationsetName];
  }

  async getGeneset(genesetName: string) {
    const _dataId = this.dataId;
    if (this.uns.customGenesets) {
      return this.uns.customGenesets;
    }
    const { data: newGeneSets } = await requestVisualData(this.dataId, {
      component: Component.UNS,
      key_path: ['customGenesets'],
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    this.uns.customGenesets = newGeneSets || {};
    return this.uns.customGenesets[genesetName];
  }

  async getFate(embeddingKey: string, xDimensionName: string, yDimensionName: string) {
    const _dataId = this.dataId;
    const { data: fate } = await requestVisualData(this.dataId, {
      component: Component.CUSTOM,
      req: 'fate',
      embedding_key: embeddingKey,
      x_dimension_name: xDimensionName,
      y_dimension_name: yDimensionName,
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    return fate;
  }

  async editUns(keyPath: string[], value: any) {
    const _dataId = this.dataId;
    if (keyPath.length === 0) {
      throw Error('keyPath is empty');
    }
    await requestEditVisualData(this.dataId, {
      component: Component.UNS,
      key_path: keyPath,
      value: value,
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    let ptr = this.uns as any;
    keyPath.slice(0, -1).forEach((key) => {
      const nextPtr = ptr[key];
      if (!nextPtr) {
        ptr[key] = {};
      }
      ptr = ptr[key];
    });
    ptr[keyPath[keyPath.length - 1]] = value;
  }

  async deleteUns(keyPath: string[]) {
    const _dataId = this.dataId;
    if (keyPath.length === 0) {
      throw Error('keyPath is empty');
    }
    await requestDeleteVisualData(this.dataId, {
      component: Component.UNS,
      key_path: keyPath,
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    let ptr = this.uns as any;
    keyPath.slice(0, -1).forEach((key) => {
      const nextPtr = ptr[key];
      if (!nextPtr) {
        ptr[key] = {};
      }
      ptr = ptr[key];
    });
    delete ptr[keyPath[keyPath.length - 1]];
  }

  async renameUns(keyPath: string[], oldKey: string, newKey: string) {
    const _dataId = this.dataId;
    if (keyPath.length === 0) {
      throw Error('keyPath is empty');
    }
    await requestRenameVisualData(this.dataId, {
      component: Component.UNS,
      key_path: keyPath,
      new_key: newKey,
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    let ptr = this.uns as any;
    keyPath.forEach((key) => {
      const nextPtr = ptr[key];
      if (!nextPtr) {
        ptr[key] = {};
      }
      ptr = ptr[key];
    });
    ptr[newKey] = ptr[oldKey];
    delete ptr[oldKey];
  }

  async addObsCol(colName: string, col: string[], dtype: string) {
    const _dataId = this.dataId;
    await requestAddVisualData(this.dataId, {
      component: Component.OBS,
      key: colName,
      col: col,
      dtype: dtype,
    });
    if (_dataId !== this.dataId) {
      throw new DataOutdatedError('data outdated!');
    }
    this.obsDataframe[colName] = DataCol.from(col);
  }
}

export const cellSelectorAdata = new Anndata();
