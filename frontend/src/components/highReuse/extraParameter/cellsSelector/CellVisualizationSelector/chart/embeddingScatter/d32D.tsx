import { graphUsedOccasion } from '@/constants/graphUsedOccasion';
// import { ChartOperationMode } from '@/constants/visualPanel';
import { ColorMode, DimensionSourceType, EmbeddingD3ChartOptions } from '@/constants/cellSelector';
// import { SelectionPolygon } from '@/interfaces/scatter';
import { cellSelectorAdata } from '@/util/anndata';
import { combineColorToAlphaCol, mixColorCols, scaleGradientColorCol } from '@/util/colorTool';
import { meanCols } from '@/util/colTool';
import { computeBrushedFlagTable, computeCentreLabels } from '@/util/scatterTool';
import { summaryContinuousCol, summaryObsCategory } from '@/util/summary';
// import windowListener from '@/util/windowListener';
import { DataCol } from '@/interfaces/col';
import { SelectionPolygon } from '@/interfaces/scatter';
import { getUuid } from '@/util/common';
import windowListener from '@/util/windowListener';
import * as d3 from 'd3';
import { useEffect, useRef, useState } from 'react';
import { useModel } from 'umi';
import { CentreLabelsLayer } from './d32DLayers/centreLabelsLayer';
import { LegendLayer } from './d32DLayers/legendLayer';
import { OperationLayer } from './d32DLayers/operationLayer';
import { PointsLayer } from './d32DLayers/pointsLayer';
import { cellSelectorFilter as cellFilter } from '@/util/cellFilter';

export const EmbeddingD32DScatter = (props: any) => {
  const { occasion, childComponentRef } = props;

  // const childComponentRef = useRef(null as null | HTMLDivElement);

  const uniqueFlag = useRef(null as null | string);

  const axisContainerRef = useRef(null as null | SVGSVGElement);

  const [chartSize, setChartSize] = useState({ width: 0, height: 0 });

  const [scaledXyCols, setScaledXyCols] = useState(null as null | [DataCol, DataCol]);

  const [pointsColorTable, setPointsColorTable] = useState(null as null | DataCol);

  const [centreLabelLayerLabelPointList, setCentreLabelLayerLabelPointList] = useState(
    [] as [number, number, string][],
  );

  const [isMaskedFnPack, setIsMaskedFnPack] = useState({
    isMaskedFn: () => false as boolean,
  });

  const [scales, setScales] = useState(
    null as null | {
      xScale: d3.ScaleLinear<number, number>;
      yScale: d3.ScaleLinear<number, number>;
    },
  );

  const [pointsLayerFreezed, setPointsLayerFreezed] = useState(false);

  const [transform, setTransform] = useState(d3.zoomIdentity);

  const {
    open: isVisualPanelOpen,
    colorMode,
    colorKey,
    dimensions,
    chartOperationMode,
    categoryColorDict,
    continuousColorDict,
    geneColorDict,
    selectionPolygon,
    chartShowLabels,
    setSelectionPolygon,
    brushSelectedTable,
    setBrushSelectedTable,
    highlightedTable,
    cellFilterVersionUuid,
    chartOptionDic,
    setChartOptionDic,
    currentOptionsBarExpanded,
    geneColorMode,
    xColAvgMonochrome,
    xColMonochrome,
    genesets,
  } = useModel('cellSelect');

  const [chartOptions, setChartOptions] = useState(EmbeddingD3ChartOptions);
  const [legendData, setLegendData] = useState<any>();

  const [legendLayout, setLegendLayout] = useState({ left: 0, top: 0, width: 0, height: 0 });

  const {
    name,
    fontSize,
    lineColor,
    componentSize,
    backgroundColor,
    aspectRatio,
    fontColor,
    lineWeight,
    fontFamily,
    axisOfDistance,
    xLabelOfDistance,
    yLabelOfDistance,
    axisSize,
    isShowLegend,
    legendHeight,
    legendWidth,
    legendCol,
    isShowBorder,
    scaleIdentification,
    obsContinuousMode,
    smallAxisSize,
    colorBarWidth,
  } = chartOptions;
  useEffect(() => {
    if (chartOptionDic.EmbeddingD3ChartOptions) {
      setChartOptions(chartOptionDic.EmbeddingD3ChartOptions);
    }
  }, [chartOptionDic]);

  const computeIsMaskedFn = () => {
    const isMaskedByBrushSelectionFn = !brushSelectedTable
      ? () => false
      : (index: number) => !brushSelectedTable.at(index);
    const cellFilterBasicNumber = cellFilter?.getBasicNumber() as number;
    const cellFilterQueryTable = cellFilter?.getQueryTable() as number[];
    const isMaskedByCellFilterFn = (index: number) =>
      cellFilterQueryTable[index] < cellFilterBasicNumber;
    return (index: number) => {
      return isMaskedByBrushSelectionFn(index) || isMaskedByCellFilterFn(index);
    };
  };

  const refreshIsMaskedFn = () => {
    setIsMaskedFnPack({
      isMaskedFn: computeIsMaskedFn(),
    });
  };

  const loadEmbeddingCols = async () => {
    if (!dimensions || dimensions.length === 0) return [new DataCol([]), new DataCol([])];
    const [xDim, yDim] = dimensions;
    const promises = [xDim, yDim].map(async (dimItem) => {
      if (!dimItem) {
        return new DataCol([]);
      }
      const { dimSource, dim } = dimItem;

      if (dimSource === DimensionSourceType.OBSM) {
        const splitIndex = dim.lastIndexOf('_');
        const embeddingKey = dim.slice(0, splitIndex);
        const colIndex = parseInt(dim.slice(splitIndex + 1));
        const [col] = await cellSelectorAdata.getObsm(embeddingKey, [colIndex]);
        return col;
      } else if (dimSource === DimensionSourceType.OBS) {
        return cellSelectorAdata.getObsCol(dim);
      } else if (dimSource === DimensionSourceType.X_COL) {
        // throw Error('not implemented');
        const colIndexes = await cellSelectorAdata.getIndexByVarNameList([dim]);
        const [col] = await cellSelectorAdata.getXCols(colIndexes);
        return col;
      }
    });
    const [xCol, yCol] = await Promise.all(promises);
    return [xCol, yCol];
  };

  const refreshEmbeddingCols = async () => {
    try {
      const cols = await loadEmbeddingCols();

      const [xCol, yCol] = cols as [DataCol, DataCol];
      const xColSummary = summaryContinuousCol(xCol);
      const yColSummary = summaryContinuousCol(yCol);
      // Create scales
      const xScale = d3
        .scaleLinear()
        .domain([xColSummary.min, xColSummary.max])
        .range([40, chartSize.width]);

      const yScale = d3
        .scaleLinear()
        .domain([yColSummary.min, yColSummary.max])
        .range([chartSize.height - 40, 0]);

      const projectedXCol = xCol.map((x: number) => {
        return xScale(x);
      });

      const projectedYCol = yCol.map((y: number) => {
        return yScale(y);
      });

      setScaledXyCols([projectedXCol, projectedYCol] as [DataCol, DataCol]);
      setScales({ xScale, yScale });
    } catch (e) {
      console.log(e);
    }
  };

  const computeColorTable = async () => {
    if (colorMode === ColorMode.CATEGORY_OBS && colorKey) {
      const colorBaseCol = await cellSelectorAdata.getObsCol(colorKey as string);
      return colorBaseCol?.map((item: string) => {
        const color = categoryColorDict[colorKey as string][item];
        const [r, g, b, a] = color;
        return `rgba(${r},${g},${b},${a})`;
      });
    } else if (
      colorMode === ColorMode.CONTINUOUS_OBS_MULTIPLE &&
      colorKey instanceof Array &&
      colorKey.length > 0
    ) {
      const cols: any = await Promise.all(colorKey.map((key) => cellSelectorAdata.getObsCol(key)));

      const colorCols = colorKey.map((key, index) => {
        if (!continuousColorDict[key]) return;

        const colorScale = d3
          .scaleLinear()
          .domain([0, 0.5, 1]) // positions of the three color stops
          .range([
            continuousColorDict[key][0],
            continuousColorDict[key][1],
            continuousColorDict[key][2],
          ]);

        const summary = summaryContinuousCol(cols[index]);
        const { min: minV, max: maxV } = summary;

        const getColor = d3.scaleSequential(colorScale).domain([maxV, minV]);

        const gradientColorCol = cols[index].map((value: number) => {
          return getColor(value);
        });

        return gradientColorCol;
      });
      const mixedColorCol = mixColorCols(colorCols);
      return mixedColorCol;
    } else if (
      colorMode === ColorMode.CONTINUOUS_X_COL_MULTIPLE &&
      colorKey instanceof Array &&
      colorKey.length > 0
    ) {
      const colIndexes = await cellSelectorAdata.getIndexByVarNameList(colorKey as string[]);
      const cols = await cellSelectorAdata.getXCols(colIndexes);

      const colorCols = cols.map((col, index) => {
        const color = geneColorDict[colorKey[index]] || [
          'rgba(255,255,255,1)',
          'rgba(255,255,255,1)',
          'rgba(255,255,255,1)',
        ];
        const colorScale = d3
          .scaleLinear()
          .domain([0, 0.5, 1]) // positions of the three color stops
          .range([color[0], color[1], color[2]]);

        const summary = summaryContinuousCol(col);
        const { min: minV, max: maxV } = summary;
        const getColor = d3.scaleSequential(colorScale).domain([maxV, minV]);

        const gradientColorCol = col.map((value: number) => {
          return getColor(value);
        });
        return gradientColorCol;
      });
      const mixedColorCol = mixColorCols(colorCols);
      return mixedColorCol;
    } else if (colorMode === ColorMode.CONTINUOUS_X_COL_AVG && !!colorKey) {
      const geneset = genesets[colorKey as string];
      const geneList = geneset.genes.map((item) => {
        return item.name;
      });

      const colIndexes = await cellSelectorAdata.getIndexByVarNameList(geneList);

      const cols = await cellSelectorAdata.getXCols(colIndexes);

      const meanCol = meanCols(cols);
      const summary = summaryContinuousCol(meanCol);
      const { min: minV, max: maxV } = summary;

      return scaleGradientColorCol(minV, maxV, meanCol, geneColorMode);
    } else if (colorMode === ColorMode.CONTINUOUS_X_COL_AVG_MONOCHROME && !!colorKey) {
      const geneset = genesets[colorKey as string];
      const geneList = geneset.genes.map((item) => {
        return item.name;
      });
      const colIndexes = await cellSelectorAdata.getIndexByVarNameList(geneList);
      const cols = await cellSelectorAdata.getXCols(colIndexes);

      const meanCol = meanCols(cols);
      const colorCols = [meanCol].map((col: DataCol) => {
        const color = xColAvgMonochrome[colorKey as string];
        return combineColorToAlphaCol(color, col);
      });

      const mixedColorCol = mixColorCols(colorCols);

      return mixedColorCol;
    } else if (colorMode === ColorMode.CONTINUOUS_XCOL && !!colorKey) {
      const colIndexes = await cellSelectorAdata.getIndexByVarNameList([colorKey] as string[]);
      const cols = await cellSelectorAdata.getXCols(colIndexes);
      const meanCol = meanCols(cols);
      const summary = summaryContinuousCol(meanCol);
      const { min: minV, max: maxV } = summary;
      return scaleGradientColorCol(minV, maxV, meanCol, geneColorMode);
    } else if (colorMode === ColorMode.CONTINUOUS_XCOL_MONOCHROME && !!colorKey) {
      const colIndexes = await cellSelectorAdata.getIndexByVarNameList([colorKey] as string[]);
      const cols = await cellSelectorAdata.getXCols(colIndexes);
      const colorCols = cols.map((col) => {
        const color = xColMonochrome[colorKey as string];
        return combineColorToAlphaCol(color, col);
      });
      const mixedColorCol = mixColorCols(colorCols);
      return mixedColorCol;
    }
    return null;
  };

  const refreshColorTable = async () => {
    const colorTable = await computeColorTable();

    setPointsColorTable(colorTable as null | DataCol);
  };

  const refreshCentreLabels = async () => {
    if (colorMode !== ColorMode.CATEGORY_OBS || !colorKey || !chartShowLabels) {
      return [];
    }
    const [xCol, yCol] = await loadEmbeddingCols();
    const clusterCol = await cellSelectorAdata.getObsCol(colorKey);
    const labelPointList = computeCentreLabels(xCol, yCol, clusterCol);
    setCentreLabelLayerLabelPointList(labelPointList);
  };

  const computeLegend = async () => {
    if (colorMode === ColorMode.CATEGORY_OBS && colorKey) {
      const colorBaseCol = await cellSelectorAdata.getObsCol(colorKey as string);
      const cellTypeSummary = summaryObsCategory(colorBaseCol as DataCol);
      const data: any = cellTypeSummary.clusters.map((clusterItem: string) => {
        const rawColor = categoryColorDict[colorKey][clusterItem];
        const color = `rgba(${rawColor[0]}, ${rawColor[1]}, ${rawColor[2]}, 1)`;
        return {
          name: clusterItem,
          color: color,
        };
      });
      return {
        data,
        height: Math.ceil(data.length / legendCol) * legendHeight,
        width: legendWidth * legendCol,
      };
    } else if (
      colorMode === ColorMode.CONTINUOUS_OBS_MULTIPLE &&
      colorKey instanceof Array &&
      colorKey.length > 0
    ) {
      const dataPromises: any = colorKey.map(async (item: any) => {
        const column = await cellSelectorAdata.getObsCol(item);
        if (!column) {
          throw new Error('column is null');
        }
        const summary = summaryContinuousCol(column);
        const { min: minV, max: maxV } = summary;

        const colorScale = d3
          .scaleLinear()
          .domain([0, 0.5, 1]) // positions of the three color stops
          .range([
            continuousColorDict[item][0],
            continuousColorDict[item][1],
            continuousColorDict[item][2],
          ]);
        return {
          name: item,
          colorScale: colorScale,
          min: minV,
          max: maxV,
        };
      });
      const data = await Promise.all(dataPromises);
      if (obsContinuousMode === 'LegendByContinuous') {
        return {
          data,
          height: Math.ceil(data.length / legendCol) * legendHeight,
          width: legendWidth * legendCol,
        };
      } else {
        return {
          data,
          height: 150,
          width: colorBarWidth * data.length,
        };
      }
    } else if (
      colorMode === ColorMode.CONTINUOUS_X_COL_MULTIPLE &&
      colorKey instanceof Array &&
      colorKey.length > 0
    ) {
      const colIndexes = await cellSelectorAdata.getIndexByVarNameList(colorKey as string[]);
      const cols = await cellSelectorAdata.getXCols(colIndexes);

      const updatedColorCols = cols.map((col, index) => {
        const color = geneColorDict[colorKey[index]] || [
          'rgba(255,255,255,1)',
          'rgba(255,255,255,1)',
          'rgba(255,255,255,1)',
        ];
        const colorScale = d3
          .scaleLinear()
          .domain([0, 0.5, 1]) // positions of the three color stops
          .range([color[0], color[1], color[2]]);

        const summary = summaryContinuousCol(col);
        const { min: minV, max: maxV } = summary;

        return {
          name: colorKey[index],
          colorScale: colorScale,
          min: minV,
          max: maxV,
        };
      });

      return {
        data: updatedColorCols,
        height: 150,
        width: colorBarWidth * updatedColorCols.length,
      };
    } else if (colorMode === ColorMode.CONTINUOUS_X_COL_AVG && !!colorKey) {
      const geneset = genesets[colorKey as string];
      const geneList = geneset.genes.map((item) => {
        return item.name;
      });

      const colIndexes = await cellSelectorAdata.getIndexByVarNameList(geneList);
      const cols = await cellSelectorAdata.getXCols(colIndexes);
      const meanCol = cols[0].map((val: number, i: number) => {
        const sum = cols.reduce((acc: number, col: DataCol) => {
          return acc + col?.at(i);
        }, 0);
        return sum / cols.length;
      });
      const summary = summaryContinuousCol(meanCol);
      const { min: minV, max: maxV } = summary;
      return { data: { min: minV, max: maxV }, width: colorBarWidth, height: 150 };
    } else if (colorMode === ColorMode.CONTINUOUS_X_COL_AVG_MONOCHROME && !!colorKey) {
      const geneset = genesets[colorKey as string];
      const geneList = geneset.genes.map((item) => {
        return item.name;
      });
      const colIndexes = await cellSelectorAdata.getIndexByVarNameList(geneList);
      const cols = await cellSelectorAdata.getXCols(colIndexes);

      const meanCol = meanCols(cols);
      const summary = summaryContinuousCol(meanCol);
      const { min: minV, max: maxV } = summary;
      const rawColor = xColAvgMonochrome[colorKey as string];
      const color = `rgba(${rawColor[0]}, ${rawColor[1]}, ${rawColor[2]}, 1)`;
      const data = [
        {
          name: colorKey,
          color: color,
          minV: minV,
          maxV: maxV,
        },
      ];
      return {
        data,
        height: 150,
        width: colorBarWidth * data.length,
      };
    } else if (colorMode === ColorMode.CONTINUOUS_XCOL && !!colorKey) {
      const colIndexes = await cellSelectorAdata.getIndexByVarNameList([colorKey] as string[]);
      const cols = await cellSelectorAdata.getXCols(colIndexes);
      const meanCol = meanCols(cols);
      const summary = summaryContinuousCol(meanCol);
      const { min: minV, max: maxV } = summary;
      return { data: { min: minV, max: maxV }, width: colorBarWidth, height: 150 };
    } else if (colorMode === ColorMode.CONTINUOUS_XCOL_MONOCHROME && !!colorKey) {
      const colIndexes = await cellSelectorAdata.getIndexByVarNameList([colorKey] as string[]);
      const cols = await cellSelectorAdata.getXCols(colIndexes);
      const meanCol = meanCols(cols);
      const summary = summaryContinuousCol(meanCol);
      const { min: minV, max: maxV } = summary;
      const rawColor = xColMonochrome[colorKey as string];
      const color = `rgba(${rawColor[0]}, ${rawColor[1]}, ${rawColor[2]}, 1)`;
      const data = [
        {
          name: colorKey,
          color: color,
          minV: minV,
          maxV: maxV,
        },
      ];
      return { data: data, width: colorBarWidth, height: 150 };
    }
    return {
      data: [],
      width: 0,
      height: 0,
    };
  };
  useEffect(() => {
    const updateLegendData = async () => {
      const { data, width, height } = await computeLegend();

      setLegendData(data);
      setLegendLayout({
        ...legendLayout,
        width,
        height,
      });
    };
    updateLegendData();
  }, [
    colorMode,
    colorKey,
    chartSize,
    categoryColorDict,
    continuousColorDict,
    xColMonochrome,
    xColAvgMonochrome,
    geneColorDict,
  ]);

  const onResize = () => {
    const container: HTMLDivElement | null = childComponentRef.current;
    if (!container) {
      return;
    }
    let width = container.clientWidth;

    let height = container.clientHeight;

    if (aspectRatio * container.clientWidth < container.clientHeight) {
      height = aspectRatio * container.clientWidth;
    } else if (aspectRatio * container.clientWidth > container.clientHeight) {
      width = container.clientHeight / aspectRatio;
    }
    setChartSize({
      width: width,
      height: height,
    });
  };

  const init = () => {
    uniqueFlag.current = getUuid();
    windowListener.register('resize', uniqueFlag.current, onResize);
  };

  const del = () => {
    windowListener.unregister('resize', uniqueFlag.current as string);
  };

  useEffect(() => {
    init();
    return () => {
      del();
    };
  }, []);

  useEffect(() => {
    refreshCentreLabels();
  }, [chartSize, chartShowLabels, colorMode, colorKey]);

  useEffect(() => {
    const container: HTMLDivElement | null = childComponentRef.current;
    if (!container) {
      return;
    }

    let width = container.clientWidth;

    let height = container.clientHeight;

    if (aspectRatio * container.clientWidth < container.clientHeight) {
      height = aspectRatio * container.clientWidth;
    } else if (aspectRatio * container.clientWidth > container.clientHeight) {
      width = container.clientHeight / aspectRatio;
    }
    setChartSize({
      width: width,
      height: height,
    });
  }, [childComponentRef.current, currentOptionsBarExpanded, chartOptionDic]);

  const updateSelectionPolygon = async (polygon: [number, number][] | null) => {
    if (!polygon) {
      setSelectionPolygon(new SelectionPolygon([]));
      setBrushSelectedTable(null);
      return;
    }
    const [xCol, yCol] = await loadEmbeddingCols();
    const selectionPolygon = new SelectionPolygon(polygon);
    const newBrushedFlagTable = computeBrushedFlagTable(xCol, yCol, selectionPolygon);
    setSelectionPolygon(selectionPolygon);
    setBrushSelectedTable(newBrushedFlagTable);
  };

  useEffect(() => {
    // console.log('dimensions', dimensions);
    // console.log('chartSize', chartSize);
    if (isVisualPanelOpen) {
      refreshEmbeddingCols();
    }
  }, [dimensions, chartSize, isVisualPanelOpen]);
  // }, [dimensions, chartSize]);

  useEffect(() => {
    refreshColorTable();
  }, [
    colorKey,
    colorMode,
    categoryColorDict,
    continuousColorDict,
    xColAvgMonochrome,
    xColMonochrome,
    geneColorMode,
    geneColorDict,
  ]);

  useEffect(() => {
    if (isVisualPanelOpen && occasion === graphUsedOccasion.THUMBNAIL) {
      setPointsLayerFreezed(true);
    } else {
      setPointsLayerFreezed(false);
    }
  }, [isVisualPanelOpen, occasion]);

  useEffect(() => {
    refreshIsMaskedFn();
  }, [cellFilterVersionUuid, brushSelectedTable]);

  useEffect(() => {
    if (!axisContainerRef.current || !scales) {
      return;
    }
    const svg = d3.select(axisContainerRef.current);
    if (axisSize == 'default') {
      svg.selectAll('*').remove();
      const xAxis = d3
        .axisBottom(transform.rescaleX(scales?.xScale))
        .tickSizeOuter(0)
        .tickPadding(axisOfDistance);
      if (scaleIdentification) {
        xAxis.tickFormat('');
      }
      svg
        .append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0, ${chartSize.height - 40})`)
        .call(xAxis);
      const yAxis = d3
        .axisLeft(transform.rescaleY(scales?.yScale))
        .tickSizeOuter(0)
        .tickPadding(axisOfDistance);

      if (scaleIdentification) {
        yAxis.tickFormat('');
      }
      svg.append('g').attr('class', 'y-axis').attr('transform', 'translate(60, 0)').call(yAxis);
      svg.selectAll('.x-axis path').attr('stroke', lineColor).attr('stroke-width', lineWeight);
      // Update x-axis label text
      svg.selectAll('.x-axis line').style('stroke', lineColor).attr('stroke-width', lineWeight);
      svg
        .selectAll('.x-axis text')
        .style('stroke', lineColor)
        .attr('stroke-width', lineWeight / 2);
      svg.selectAll('.y-axis path').attr('stroke', lineColor).attr('stroke-width', lineWeight);
      svg.selectAll('.y-axis line').style('stroke', lineColor).attr('stroke-width', lineWeight);
      svg
        .selectAll('.y-axis text')
        .style('stroke', lineColor)
        .attr('stroke-width', lineWeight / 2);
      // const xAxisLabelGroup = svg.select('.x-axis-label');
      // xAxisLabelGroup.selectAll('*').remove(); // clear existing labels

      svg
        .append('text')
        .attr('x', chartSize.width / 2)
        .attr('y', chartSize.height - 10 - xLabelOfDistance)
        .attr('text-anchor', 'middle')
        .style('font-size', fontSize.xy)
        .style('fill', fontColor.xy)
        .style('font-family', fontFamily.xy)
        .text(name.x);
      // Update y-axis label text
      const yAxisLabelGroup = svg.select('.y-axis-label');
      yAxisLabelGroup.selectAll('*').remove();
      svg
        .append('text')
        .attr('x', -chartSize.height / 2)
        .attr('y', 20 + yLabelOfDistance)
        .attr('transform', 'rotate(-90)')
        .style('font-size', fontSize.xy)
        .style('fill', fontColor.xy)
        .style('font-family', fontFamily.xy)
        .text(name.y);
    } else {
      const arrowheadPath = 'M0,0 L12,6 L0,12 Z';
      const width = +svg.attr('width');
      const height = +svg.attr('height');
      svg.selectAll('*').remove();
      svg
        .append('line')
        .attr('x1', 40)
        .attr('y1', height - 40)
        .attr('x2', width * smallAxisSize)
        .attr('y2', height - 40)
        .attr('stroke', 'black')
        .style('stroke', lineColor)
        .attr('stroke-width', lineWeight)
        .attr('marker-end', 'url(#arrowheadX)');

      // Draw positive y-axis arrow

      svg
        .append('line')
        .attr('x1', 40)
        .attr('y1', width - 40)
        .attr('x2', 40)
        .attr('y2', width * (1 - smallAxisSize))
        .attr('stroke', 'black')
        .style('stroke', lineColor)
        .attr('stroke-width', lineWeight)
        .attr('marker-end', 'url(#arrowheadY)');

      // Define arrowhead markers

      svg
        .append('defs')
        .append('marker')
        .attr('id', 'arrowheadX')
        .attr('refX', 6)
        .attr('refY', 6)
        .attr('markerWidth', 250)
        .attr('markerHeight', 250)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', arrowheadPath)
        .attr('fill', lineColor);

      svg
        .append('defs')
        .append('marker')
        .attr('id', 'arrowheadY')
        .attr('refX', 3)
        .attr('refY', 6)
        .attr('markerWidth', 250)
        .attr('markerHeight', 250)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', arrowheadPath)
        .attr('fill', lineColor);
      // Add x-axis label
      svg
        .append('text')
        .attr('x', width / 4 + 5)
        .attr('y', height - 10 - xLabelOfDistance)
        .attr('text-anchor', 'middle')
        .style('font-size', fontSize.xy)
        .style('fill', fontColor.xy)
        .style('font-family', fontFamily.xy)
        .text(name.x);

      // Add y-axis label
      svg
        .append('text')
        .attr('x', -height / 4 + 20)
        .attr('y', width / 2 + 10 + yLabelOfDistance)
        .attr('text-anchor', 'middle')
        .style('font-size', fontSize.xy)
        .style('fill', fontColor.xy)
        .style('font-family', fontFamily.xy)
        .attr('transform', 'rotate(-90, 10, ' + width / 2 + ')')
        .text(name.y);
    }
  }, [chartSize, scales, transform, chartOptionDic, colorKey]);

  useEffect(() => {
    if (!chartOptionDic?.EmbeddingD3ChartOptions?.name || !dimensions) {
      return;
    }
    const { EmbeddingD3ChartOptions: embedding2dChartOptionDic } = chartOptionDic;
    const [xDim, yDim] = dimensions;
    if (!xDim || !yDim) {
      return;
    }
    const newEmbedding2dChartOptionDic = {
      ...embedding2dChartOptionDic,
      name: {
        x: xDim.dim,
        y: yDim.dim,
      },
    };
    setChartOptionDic({
      ...chartOptionDic,
      EmbeddingD3ChartOptions: newEmbedding2dChartOptionDic,
    });
  }, [dimensions]);

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',

        backgroundColor: backgroundColor,
      }}
      ref={childComponentRef}
    >
      <PointsLayer
        chartSize={chartSize}
        scales={scales}
        scaledXyCols={scaledXyCols}
        transform={transform}
        componentSize={componentSize}
        colorJudge={{
          colorTable: pointsColorTable,
          annotatedTable: null,
        }}
        sizeJudge={{
          highlightedTable: highlightedTable,
          isMaskedFn: isMaskedFnPack.isMaskedFn,
        }}
        freeze={pointsLayerFreezed}
      />
      <CentreLabelsLayer
        chartSize={chartSize}
        scales={scales}
        enable={chartShowLabels}
        labelPointList={centreLabelLayerLabelPointList}
        transform={transform}
        fontSize={fontSize.label}
        fontColor={fontColor.compontentLabel}
        fontFamily={fontFamily.compontentLabel}
      />
      {colorMode !== ColorMode.NO_COLOR && isShowLegend && (
        <LegendLayer
          chartSize={chartSize}
          scales={scales}
          legendData={legendData}
          chartOptions={chartOptions}
          legendLayout={legendLayout}
        />
      )}

      {/* {chartOperationMode === ChartOperationMode.BRUSH && (
        <LassoLayer
          chartSize={chartSize}
          scales={scales}
          selectionPolygon={selectionPolygon}
          updateSelectionPolygon={updateSelectionPolygon}
          enable={true}
          transform={transform}
        />
      )}
      {chartOperationMode === ChartOperationMode.DRAG && (
        <ZoomLayer chartSize={chartSize} setTransform={setTransform} transform={transform} />
      )} */}
      <OperationLayer
        chartSize={chartSize}
        setTransform={setTransform}
        transform={transform}
        scales={scales}
        selectionPolygon={selectionPolygon}
        updateSelectionPolygon={updateSelectionPolygon}
        chartOperationMode={chartOperationMode}
        setLegendLayout={setLegendLayout}
        legendLayout={legendLayout}
        isShowBorder={isShowBorder}
      />
      {chartOptionDic?.EmbeddingD3ChartOptions?.isShowAxis && (
        <svg
          ref={axisContainerRef}
          height={chartSize.height}
          width={axisSize === 'default' ? chartSize.width : chartSize.height}
          style={{
            position: 'relative',
            zIndex: 50,
          }}
        />
      )}
    </div>
  );
};
