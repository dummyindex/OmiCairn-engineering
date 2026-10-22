import type { DataCol } from './col';

export interface DataStructure {
  shape: [number, number];
  obs: {
    key: string;
    dtype: string;
  }[];
  var: {
    key: string;
    dtype: string;
  }[];
  obsm: {
    shape: number[];
    keys: string[];
  };
  varm: {
    shape: number[];
    keys: string[];
  };
  obsp: string[];
  varp: string[];
  layers: string[];
}

export type UniqueKeyCol = DataCol;

export type ObsDataframe = Record<string, DataCol>;

export type VarDataframe = Record<string, DataCol>;

export type Matrix = DataCol[];

export type Layers = Record<string, Matrix>;

export type OBSM = Record<string, Matrix>;

export type VARM = Record<string, Matrix>;

export type OBSP = Record<string, Matrix>;

export type VARP = Record<string, Matrix>;

export type UNS = Record<string, any>;
