export type CategoryColorDict = Record<string, Record<string, number[]>>;

export type ContinuousColorDict = Record<string, number[]>;

export type GeneColorDict = Record<string, string[]>;

export type Cellsets = {
  name: string;
  description: string;
  cells: {
    [geneName: string]: string;
    description: string;
  };
};

export type Genesets = {
  name: string;
  description: string;
  genes: {
    [geneName: string]: string;
    description: string;
  };
};

export type GlobalChartOptions = {
  bgColor: string; // rgba
  elementSizeRate: number; // 0.1 ~ 1
  elementOpacity: number; // 0 ~ 1
  showElementBorder: boolean; // true or false
  elementBorderColor: string; // rgba
  fontColor: string; // rgba
};

export type EmbeddingChartOptionsType = {
  name: { x: string; y: string };
  fontSize: { xy: number; label: number; legend: number };
  fontFamily: { xy: string; compontentLabel: string; legend: string };
  fontColor: { xy: string; compontentLabel: string; legend: string };
  lineWeight: number;
  lineColor: string;
  componentSize: number;
  backgroundColor: string;
  aspectRatio: number;
};

export type DifferenceSelected = Record<string, string[]>;

export type VitessceState = {
  id: string;
  status: string;
  name: string;
  queryString: string;
  statusReason: string;
  createdTime: string;
  options: null | {
    obs_cols: string[];
    var_cols: string[];
    obsm_cols: string[];
    uns_spatial_key: string;
    image: string;
  };
};

export enum VitessceStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
}
