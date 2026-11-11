export const DataListFetchMode = {
  PUBLIC: 'public',
  ALL: 'all',
  IMPORTED: 'imported',
  UPLOADED: 'uploaded',
  COLLECTED: 'collected',
};

export const UploadType = {
  ASSEMBLE: 'assemble',
  ANNDATA: 'anndata',
  FASTQ: 'fastq',
  OUTS: '10x',
  SPACERANGER_COUNT: 'spaceranger_count',
  SPACERANGER_AGGR: 'spaceranger_aggr',
  THIRD_PARTY_DATA: 'third_party_data',
  SEURAT_OBJECT_RDS: 'seurat_object_rds',
  GENERAL: 'general',
};

export const UploadFromType = {
  FROMASSEMBLED: 'from assembled',
  FROMUPLOADEDDIRECTLY: 'from uploaded directly',
  FROMFASTQ: 'from fastq',
  FROM10X: 'from 10x',
  FROM_SPACERANGER_COUNT: 'from space ranger count',
  FROM_SPACERANGER_AGGR: 'from space ranger aggr',
  THIRD_PARTY_DATA: 'third_party_data',
  FROMSEURATOBJECTRDS: 'from seurat object rds',
};

export const ComponentType = {
  VAR: 'var',
  OBS: 'obs',
  X: 'X',
  OBSM: 'obsm',
  OBSP: 'obsp',
  VARM: 'varm',
  VARP: 'varp',
  LAYERS: 'layers',
  LAYER_UNSPLICED: 'unspliced',
  LAYER_SPLICED: 'spliced',
};

export const DataState = {
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  PREHANDLING: 'prehandling',
  ERROR: 'error',
  OK: 'ok',
};
