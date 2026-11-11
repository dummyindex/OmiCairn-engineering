export const CellLeftMenu = {
  OBS: 'obs',
  GENE: 'gene',
};

export const ColorMode = {
  NO_COLOR: 'no color',
  CATEGORY_OBS: 'category obs', //obs
  CONTINUOUS_OBS_MULTIPLE: 'continuous obs multiple', // continuous-value coloring
  CONTINUOUS_XCOL: 'continuous xcol', // coloring by a gene within a geneset
  CONTINUOUS_XCOL_MONOCHROME: 'continuous xcol monochrome', // single-color coloring by a gene within a geneset
  CONTINUOUS_X_COL_AVG: 'continuous xcol avg', // geneset coloring
  CONTINUOUS_X_COL_AVG_MONOCHROME: 'continuous xcol avg monochrome',
  CONTINUOUS_X_COL_TOP_GENE: 'continuous xcol top gene', //top gene
  CONTINUOUS_X_COL_MULTIPLE: 'continuous xcol multiple', // obs-gene multi-color coloring
};

export const ChartOperationMode = {
  BRUSH: 'brush',
  DRAG: 'drag',
  // CLICK:'click'
};

export const LeftOperationMode = {
  ANNOTATION: 'annotation',
  CELLSET: 'cellset',
};

export const ColorPalette = [
  '#FF0000',
  '#FFA500',
  '#FFFF00',
  '#008000',
  '#00FFFF',
  '#0000FF',
  '#800080',
  '#FFC0CB',
  '#8B0000',
  '#FF7F50',
  '#FFD700',
  '#32CD32',
  '#87CEEB',
  '#8A2BE2',
  '#FF1493',
  '#FF6347',
  '#FFA07A',
  '#ADFF2F',
  '#4682B4',
  '#4B0082',
];

export const EmbeddingMode = {
  TWO_D: '2d',
  THREE_D: '3d',
};

export const DefaultGlobalChartOptions = {
  bgColor: 'rgba(255, 255, 255, 1)',
  elementSizeRate: 5,
  elementOpacity: 1,
  showElementBorder: false,
  elementBorderColor: 'rgba(0, 0, 0, 1)',
  fontColor: 'rgba(0, 0, 0, 1)',
};

export const EmbeddingD3ChartOptions = {
  name: { x: 'xLabel', y: 'yLabel' },
  fontSize: { xy: 16, label: 16, legend: 16 },
  fontFamily: { xy: 'Arial', compontentLabel: 'Arial', legend: 'Arial' },
  fontColor: { xy: '#000', compontentLabel: '#000', legend: '#000' },
  scaleIdentification: false,
  lineWeight: 1,
  lineColor: '#000',
  componentSize: 1,
  backgroundColor: '#fff',
  aspectRatio: 0.56,
  isShowAxis: true,
  isShowLegend: true,
  axisOfDistance: 5,
  xLabelOfDistance: 0,
  yLabelOfDistance: 0,
  axisSize: 'small',
  smallAxisSize: 0.5,
  legendShape: 'round',
  LegendDirection: 'vertical',
  legendWidth: 200,
  colorBarWidth: 100,
  colorBarDecimal: 2,
  legendHeight: 25,
  legendRow: 0,
  legendCol: 1,
  isShowBorder: false,
  legendTop: 0,
  legendLeft: 100,
  obsContinuousMode: 'color bar',
  backgroundAlpha: 1,
};

export const DEFAULT_SCATTER_COLOR = 'rgba(50,50,50,1)';

export const ChartType = {
  EMBEDDING: 'embedding',
  // CALCULATEQCMETRICS: 'calculate qc metrics',
  // DPTPSEUDOTIME: 'dpt',
  // RANKGENESGROUPSHEATMAP: 'rank genes groups',
  // DOTPLOT: 'dotplot',
  // VIOLIN: 'violin',
  FIGURE: 'figure',
  DYNAMICS: 'dynamics',
  VECTORFIELD: 'vector_field',
  GENEFRACTION: 'gene_fraction',
  FATE: 'fate',
  STATEGRAPH: 'state_graph',
  CELLTYPE_PROPORTION: 'proportion',
  SPEED: 'speed',
  ACCELERATION: 'acceleration',
  CURVATURE: 'curvature',
  DIVERGENCE: 'divergence',
};

export const DimensionSourceType = {
  OBS: 'obs',
  OBSM: 'obsm',
  X_COL: 'xcol',
};

export const ButtonRankGenesId = '9';
export const ButtonTopGeneId = '58';
