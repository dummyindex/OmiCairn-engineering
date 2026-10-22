export const ParamsRenderType = {
  STR_INPUT: 'str-input',
  STR_LIST_INPUT: 'str-list-input',
  STR_OPTIONS: 'str-options',
  STR_RADIO: 'str-radio',
  STR_MULTIPLE_OPTIONS: 'str-multiple-options',
  SINGLE_GENE_SELECTOR: 'single-gene-selector',
  SINGLE_CELL_SELECTOR: 'single-cell-selector',
  INT_INPUT: 'int-input',
  INT_LIST_INPUT: 'int-list-input',
  FLOAT_INPUT: 'float-input',
  BOOL_INPUT: 'bool-input',
  GENES_SELECTOR: 'genes-selector',
  CELLS_SELECTOR: 'cells-selector',
  DICT_INPUT: 'dict-input',
  DYNAMIC_DICT_INPUT: 'dynamic-dict-input',
  ORGANISM_SELECTOR: 'organism-selector',
  LIBRARIES_SELECTOR: 'libraries-selector',
  ADATA_OBS_KEY: 'adata-obs-key',
  ADATA_VAR_KEY: 'adata-var-key',
  ADATA_OBSM_KEY: 'adata-obsm-key',
  ADATA_OBSP_KEY: 'adata-obsp-key',
  ADATA_LAYER_KEY: 'adata-layers-key',
  ADATA_UNS_KEY: 'adata-uns-key',

  ADATA_OBS_KEY_LIST: 'adata-obs-key-list',
  ADATA_OBS_GROUP_LIST: 'adata-obs-group-list',
  ADATA_OBS_GROUP: 'adata-obs-group',
  DATASELECTER: 'data-selector',
  ADATA_LIST_INPUT: 'adata-list-input',
  ADATA_INPUT: 'adata-input',

  ADATA_VAR_KEY_LIST: 'adata-var-key-list',

  FILE: 'file',

  API_KEY_INPUT: 'api-key-input',
};

export const FunctionBlockType = {
  COMPUTATION: 'computation',
};

export const FunctionBlockState = {
  UNUPLOAD: 'unupload',
  PREHANDLING: 'prehandling',
  OK: 'ok',
  FAILED: 'failed',
};

export const FunctionBlockUpdateStep = {
  INPUT: 'input',
  UPLOAD: 'upload',
};

export const FunctionBlockCreateStep = {
  INPUT: 'input',
  UPLOAD: 'upload',
};

export const FBOccasion = {
  FLOW: 'flow',
  MINI_TOOL: 'mini-tool',
};

export const PresetFBs = {
  VISUAL: {
    ID: 150,
    VID: 163,
  },
};
