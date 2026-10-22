import {
  ChartOperationMode,
  ChartType,
  ColorMode,
  ColorPalette,
  DefaultGlobalChartOptions,
  DimensionSourceType,
  EmbeddingD3ChartOptions,
  EmbeddingMode,
} from '@/constants/cellSelector';
import type { DataStructure } from '@/interfaces/anndata';
import type { DataCol } from '@/interfaces/col';
import { SelectionPolygon } from '@/interfaces/scatter';
import type {
  CategoryColorDict,
  Cellsets,
  ContinuousColorDict,
  GeneColorDict,
  Genesets,
  GlobalChartOptions,
} from '@/interfaces/visualPanel';
import { cellSelectorFilter } from '@/util/cellFilter';
import React, {
  useEffect,
  //  useRef
} from 'react';
import chroma from 'chroma-js';
import * as d3 from 'd3-scale-chromatic';
import {
  // Anndata,
  cellSelectorAdata,
} from '@/util/anndata';
import {
  loadCellsets,
  loadGeneset,
  requestGetDataStructure,
  requestGetDataStructureClassification,
} from '@/request/attachedData';

const useCellSelect = () => {
  const [open, setOpen] = React.useState(false);

  // which data is selected
  const [dataId, setDataId] = React.useState<string | null>(null);
  // is panel loading
  const [loading, setLoading] = React.useState(false);

  // is panel loaded error
  const [error, setError] = React.useState(false);

  // top left search key
  const [searchKey, setSearchKey] = React.useState<string | null>(null);

  // data structure
  const [dataStructure, setCellDataStructure] = React.useState<DataStructure | null>(
    null as DataStructure | null,
  );

  // scatter color mode: no color, category obs, continuous obs multiple, continuous xcol, continuous xcol avg, continuous xcol multiple
  const [colorMode, setColorMode] = React.useState<string>(ColorMode.NO_COLOR);

  // scatter color by what: categorical obs col, continuous obs col, continuous xcol
  const [colorKey, setColorKey] = React.useState<string | string[] | null>(
    null as string | string[] | null,
  );

  // categorical obs col color dict
  const [categoryColorDict, setCategoryColorDict] = React.useState({} as CategoryColorDict);

  // continuous obs col color dict
  const [continuousColorDict, setContinuousColorDict] = React.useState({} as ContinuousColorDict);

  // geneset coloring logic
  const [xColAvgMonochrome, setXColAvgMonochrome] = React.useState({} as ContinuousColorDict);

  // gene color dict
  const [geneColorDict, setGeneColorDict] = React.useState({} as GeneColorDict);

  // coloring logic for a gene within a geneset
  const [xColMonochrome, setXColMonochrome] = React.useState({} as ContinuousColorDict);

  // current scatter embedding by which obsm key
  const [embeddingKey, setEmbeddingKey] = React.useState<string | null>(null as string | null);

  // current scatter embedding by which obsm cols
  const [dimensions, setDimensions] = React.useState<{ dimSource: string; dim: string }[]>([]);

  const [operatedDimensions, setOperatedDimensions] = React.useState<
    { dimSource: string; dim: string } | null[]
  >([null, null, null]);
  // dialog state
  const [xyzDimensions, setXyzDimensions] = React.useState<
    { dimSource: string; dim: string } | null[]
  >([null, null, null]);

  const [dimensionsLoading, setDimensionsLoading] = React.useState<boolean>(false);

  // chart operation mode: brush, drag
  const [chartOperationMode, setChartOperationMode] = React.useState<string>(
    ChartOperationMode.DRAG,
  );

  const [chartShowLabels, setChartShowLabels] = React.useState<boolean>(false);

  // brush selection polygon in scatter
  const [selectionPolygon, setSelectionPolygon] = React.useState<SelectionPolygon>(
    new SelectionPolygon([]),
  );

  // scatter x y plot dims (bottom left corner)
  const [xYPlotDims, setXYPlotDims] = React.useState<[string | null, string | null, string | null]>(
    [null, null, null],
  );

  // sets of collected cells
  const [cellsets, setCellsets] = React.useState({} as Cellsets);

  const [genesets, setGenesets] = React.useState({} as Genesets);

  // scatter embedding mode: 2d, 3d
  const [embeddingMode, setEmbeddingMode] = React.useState<string>(EmbeddingMode.THREE_D);

  // global styling parameters
  const [globalChartOptions, setGlobalChartOptions] =
    React.useState<GlobalChartOptions>(DefaultGlobalChartOptions);

  const [chartOptionDic, setChartOptionDic] = React.useState({ EmbeddingD3ChartOptions });

  // boolean array to indicate which cells are selected
  const [brushSelectedTable, setBrushSelectedTable] = React.useState<null | DataCol>(
    null as DataCol | null,
  );

  const [highlightedTable, setHighlightedTable] = React.useState<null | boolean[]>(
    null as boolean[] | null,
  );

  // cell filter handler
  const [cellFilterVersionUuid, setCellFilterVersionUuid] = React.useState<string | null>(null);

  const [activeKey, setActivekey] = React.useState<{
    name: string;
    id: number | null;
    chartName: string;
  }>({
    name: ChartType.EMBEDDING,
    id: null,
    chartName: ChartType.EMBEDDING,
  });

  const [isFillScreen, setIsFillScreen] = React.useState(false);

  // controls the right-side menu bar
  const [currentOptionsBarExpanded, setCurrentOptionsBarExpanded] = React.useState(true);

  // continuous-value gradient color scheme adjustment
  const [geneColorMode, setGeneColorMode] = React.useState(() => d3.interpolateCool);
  // gene coloring color
  const [geneColorList, setGeneColorList] = React.useState([
    'rgb(110,64,170)',
    'rgb(26,199,194)',
    'rgb(175,240,91)',
  ]);

  // DataStructure categories
  const [dataStructureClassification, setDataStructureClassification] = React.useState({});

  const [selectedCellDict, setSelectedCellDict] = React.useState({} as any);
  const [cellsetDict, setCellsetDictDict] = React.useState({} as any);

  const changeInterpolator = (colorScaleFunction) => {
    setGeneColorMode(() => colorScaleFunction);
  };

  const updateEmbedding = (embeddingKey: string) => {
    setEmbeddingKey(embeddingKey);
  };

  const updateEmbeddingDimensions = (dimensions: { dimSource: string; dim: string }[]) => {
    setOperatedDimensions(dimensions);
    setBrushSelectedTable(null);
    setSelectionPolygon(new SelectionPolygon([]));
  };

  const initPanelStateByStructure = (
    dataStructure: DataStructure,
    customColorDict: any,
    _: any,
    cellsets: any,
    genesets: any,
  ) => {
    const { obs, obsm } = dataStructure;

    if (obsm) {
      const embeddingKeys = Object.keys(obsm).filter((key) => key.startsWith('X_'));
      if (embeddingKeys.length > 0) {
        // TODO: deleted?
        updateEmbedding(embeddingKeys[0]);

        // set default dimensions
        const defaultEmbeddingKey = embeddingKeys[0];
        const cols = obsm[defaultEmbeddingKey][1];

        if (cols >= 3) {
          updateEmbeddingDimensions([
            { dimSource: DimensionSourceType.OBSM, dim: `${defaultEmbeddingKey}_0` },
            { dimSource: DimensionSourceType.OBSM, dim: `${defaultEmbeddingKey}_1` },
            { dimSource: DimensionSourceType.OBSM, dim: `${defaultEmbeddingKey}_2` },
          ]);
        } else if (cols == 2) {
          updateEmbeddingDimensions([
            { dimSource: DimensionSourceType.OBSM, dim: `${defaultEmbeddingKey}_0` },
            { dimSource: DimensionSourceType.OBSM, dim: `${defaultEmbeddingKey}_1` },
            { dimSource: DimensionSourceType.OBSM, dim: `${defaultEmbeddingKey}_umap` },
          ]);
        }
      }
    }
    let { categoryColorDict, continuousColorDict } = customColorDict;
    const { geneColorDict } = customColorDict;

    if (obs) {
      categoryColorDict = categoryColorDict || {};
      continuousColorDict = continuousColorDict || {};
      const scale = chroma.scale(ColorPalette);
      obs.forEach((obsItem: any, obsIndex: number) => {
        const { key, dtype, categories } = obsItem;
        if (dtype === 'category') {
          categoryColorDict[key] = categoryColorDict[key] || {};
          categories.forEach((categoryItem: string, index: number) => {
            if (!categoryColorDict[key][categoryItem]) {
              categoryColorDict[key][categoryItem] = scale(index / categories.length).rgba();
            }
          });
        } else if (dtype.startsWith('float')) {
          const colorArr = [1, 2, 3].map((item) => {
            return scale(obsIndex / obs.length / item).rgba();
          });

          continuousColorDict[key] = continuousColorDict[key] || [
            `rgba(${colorArr[0][0]},${colorArr[0][1]},${colorArr[0][2]},${colorArr[0][3]})`,
            `rgba(${colorArr[1][0]},${colorArr[1][1]},${colorArr[1][2]},${colorArr[1][3]})`,
            `rgba(${colorArr[2][0]},${colorArr[2][1]},${colorArr[2][2]},${colorArr[2][3]})`,
          ];
        }
      });
    }

    setCategoryColorDict(categoryColorDict);
    setContinuousColorDict(continuousColorDict);
    setXColAvgMonochrome({});
    setXColMonochrome({});
    setGeneColorDict(geneColorDict || {});

    setCellsets(cellsets);
    setGenesets(genesets);
  };

  const loadInitialInformation = async (dataId) => {
    setLoading(true);
    try {
      const [
        newDataStructure,
        customColorDict,
        customMarkerDict,
        cellsets,
        genesets,
        dataStructureClassification,
      ] = await Promise.all([
        requestGetDataStructure(dataId),
        cellSelectorAdata.getUns(['customColorDict']),
        cellSelectorAdata.getUns(['customMarkerDict']),
        loadCellsets(dataId),
        loadGeneset(dataId),
        requestGetDataStructureClassification(dataId),
      ]);

      if (!newDataStructure) {
        throw new Error('dataStructure is null');
      }

      // console.log('dataId', dataId);

      if (cellSelectorAdata.dataId !== dataId) {
        return;
      }

      setCellDataStructure(newDataStructure);
      setDataStructureClassification(dataStructureClassification);

      initPanelStateByStructure(
        newDataStructure,
        customColorDict || {},
        customMarkerDict,
        cellsets || {},
        genesets || {},
      );
      cellSelectorFilter.reset(newDataStructure.shape[0]);
      setCellFilterVersionUuid(cellSelectorFilter.getVersionUuid());

      setError(false);
    } catch (e) {
      console.log(e);
      setError(true);
    }
    setLoading(false);
  };

  const updateColorMode = (newColorMode: string, colorKey: string | string[] | null) => {
    setColorMode(newColorMode);
    if (newColorMode === ColorMode.NO_COLOR) {
      setColorKey(null);
    } else {
      setColorKey(colorKey);
    }
  };

  const updateColor = (colorBand: any[]) => {
    const { obs } = dataStructure;
    const scale = chroma.scale(colorBand);
    obs.forEach((obsItem: any, obsIndex: number) => {
      // console.log('obsItem', index / categories.length);
      const { key, dtype, categories } = obsItem;

      if (dtype === 'category') {
        categoryColorDict[key] = categoryColorDict[key] || {};
        categories.forEach((categoryItem: string, index: number) => {
          // if (!categoryColorDict[key][categoryItem]) {
          categoryColorDict[key][categoryItem] = scale(index / categories.length).rgba();
          // }
        });
      } else if (dtype.startsWith('float')) {
        const colorArr = [1, 2, 3].map((item) => {
          return scale(obsIndex / obs.length / item).rgba();
        });

        continuousColorDict[key] = continuousColorDict[key] || [
          `rgba(${colorArr[0][0]},${colorArr[0][1]},${colorArr[0][2]},${colorArr[0][3]})`,
          `rgba(${colorArr[1][0]},${colorArr[1][1]},${colorArr[1][2]},${colorArr[1][3]})`,
          `rgba(${colorArr[2][0]},${colorArr[2][1]},${colorArr[2][2]},${colorArr[2][3]})`,
        ];
      }
    });

    setCategoryColorDict({ ...categoryColorDict });
    setContinuousColorDict({ ...continuousColorDict });
  };

  const clearState = () => {
    setCellDataStructure(null);
    setDataStructureClassification({});
    setCategoryColorDict({});
    setContinuousColorDict({});
    setXColAvgMonochrome({});
    setXColMonochrome({});
    setGeneColorDict({});
    setCellsets({});
    setGenesets({});
    setEmbeddingKey(null);
    setDimensions([]);
    setColorMode(ColorMode.NO_COLOR);
    setColorKey(null);
    setBrushSelectedTable(null);
    setSelectionPolygon(new SelectionPolygon([]));
    setXYPlotDims([null, null, null]);
    setChartOperationMode(ChartOperationMode.DRAG);
    setChartShowLabels(false);
    setChartOptionDic({ EmbeddingD3ChartOptions });
    setGlobalChartOptions(DefaultGlobalChartOptions);
    cellSelectorFilter.reset();
    setCellFilterVersionUuid(cellSelectorFilter.getVersionUuid());
    setError(false);
    setLoading(false);
    setSelectedCellDict({});
    setCellsetDictDict({});
    setGeneColorList(['rgb(110,64,170)', 'rgb(26,199,194)', 'rgb(175,240,91)']);
  };

  useEffect(() => {
    const newDimensions = [
      xyzDimensions[0] ? xyzDimensions[0] : operatedDimensions[0],
      xyzDimensions[1] ? xyzDimensions[1] : operatedDimensions[1],
      xyzDimensions[2] ? xyzDimensions[2] : operatedDimensions[2],
    ];

    if (newDimensions.every((dim) => dim === null)) {
      setDimensions([]);
    } else {
      setDimensions(newDimensions);
    }
  }, [operatedDimensions, xyzDimensions]);

  useEffect(() => {
    cellSelectorAdata.clearAll();
    clearState();
    if (dataId) {
      cellSelectorAdata.setDataId(dataId);
      loadInitialInformation(dataId);
    }
  }, [dataId]);

  return {
    open,
    setOpen,

    dataId,
    setDataId,
    loading,
    error,
    dataStructure,
    setCellDataStructure,

    chartOperationMode,
    setChartOperationMode,
    chartShowLabels,
    setChartShowLabels,

    colorMode,
    categoryColorDict,
    continuousColorDict,
    xColAvgMonochrome,
    xColMonochrome,
    geneColorDict,
    // customMarkerDict,
    colorKey,
    embeddingKey,
    dimensions,
    xyzDimensions,
    searchKey,
    dimensionsLoading,
    setDimensionsLoading,
    setXyzDimensions,
    setCategoryColorDict,
    setContinuousColorDict,
    setXColAvgMonochrome,
    setXColMonochrome,
    setGeneColorDict,
    setSearchKey,

    cellsets,
    genesets,
    setCellsets,
    setGenesets,

    selectionPolygon,
    setSelectionPolygon,

    xYPlotDims,
    setXYPlotDims,

    embeddingMode,
    setEmbeddingMode,

    chartOptionDic,
    setChartOptionDic,

    globalChartOptions,
    setGlobalChartOptions,

    brushSelectedTable,
    setBrushSelectedTable,
    highlightedTable,
    setHighlightedTable,

    cellFilterVersionUuid,
    setCellFilterVersionUuid,

    activeKey,
    setActivekey,

    isFillScreen,
    setIsFillScreen,

    currentOptionsBarExpanded,
    setCurrentOptionsBarExpanded,

    // gene coloring scheme
    geneColorMode,
    setGeneColorMode,

    // dataStructure categories
    dataStructureClassification,
    setDataStructureClassification,

    geneColorList,
    setGeneColorList,

    updateColorMode,
    updateColor,

    changeInterpolator,

    updateEmbeddingDimensions,

    selectedCellDict,
    setSelectedCellDict,
    cellsetDict,
    setCellsetDictDict,

    clearState,
  };
};

export default useCellSelect;
