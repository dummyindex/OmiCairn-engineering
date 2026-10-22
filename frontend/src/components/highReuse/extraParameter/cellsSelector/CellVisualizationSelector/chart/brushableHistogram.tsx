// Adapted from cellxgene (https://github.com/chanzuckerberg/cellxgene),
// Copyright (c) Chan Zuckerberg Initiative. MIT License; see THIRD_PARTY_NOTICES.md.
import type { DataCol } from '@/interfaces/col';
import { cellSelectorAdata } from '@/util/anndata';
import { cellSelectorFilter } from '@/util/cellFilter';
import { meanCols } from '@/util/colTool';
import { memoize } from '@/util/fnTool';
import { histogramContinuous } from '@/util/histogram';
import { summaryContinuousCol } from '@/util/summary';
import windowListener from '@/util/windowListener';
import * as d3 from 'd3';
import React, { useEffect, useRef } from 'react';
import { useModel } from 'umi';
import ErrorLoading from './brushableHistogram/error';
import HistogramFooter from './brushableHistogram/footer';
import Histogram from './brushableHistogram/histogram';
import StillLoading from './brushableHistogram/loading';

interface Props {
  field: string;
  isColorAndMarkerAccessor: boolean;
  isGeneSetSummary: boolean;
  isTopGeneSetSummary: boolean;
  zebra: boolean;
  isObs: boolean;
  mini: boolean;
  hideAnno: boolean;
  loading: boolean;
  setLoading: Function;
}

const MARGIN = {
  LEFT: 10, // Space for 0 tick label on X axis
  RIGHT: 54, // space for Y axis & labels
  BOTTOM: 25, // space for X axis & labels
  TOP: 3,
};
const WIDTH = 340 - MARGIN.LEFT - MARGIN.RIGHT;
const HEIGHT = 135 - MARGIN.TOP - MARGIN.BOTTOM;
const MARGIN_MINI = {
  LEFT: 0, // Space for 0 tick label on X axis
  RIGHT: 0, // space for Y axis & labels
  BOTTOM: 0, // space for X axis & labels
  TOP: 0,
};
const WIDTH_MINI = 120 - MARGIN_MINI.LEFT - MARGIN_MINI.RIGHT;
const HEIGHT_MINI = 15 - MARGIN_MINI.TOP - MARGIN_MINI.BOTTOM;

const BrushableHistogram = (props: Props) => {
  const {
    field,
    isObs,
    isGeneSetSummary,
    isColorAndMarkerAccessor,
    zebra,
    mini,
    hideAnno,
    loading,
    setLoading,
  } = props;

  const [error, setError] = React.useState<boolean>(false);

  const [chartInfo, setChartInfo] = React.useState({} as any);

  const { genesets, setCellFilterVersionUuid, geneColorMode, colorKey } = useModel('cellSelect');

  const containerRef = useRef<HTMLDivElement>(null);

  const [width, setWidth] = React.useState<number>(200);

  // eslint-disable-next-line class-methods-use-this -- instance method allows for memoization per annotation
  const calcHistogramCache = memoize(
    (col: DataCol, newMargin, newWidth, newHeight) => {
      /*
     recalculate expensive stuff, notably bins, summaries, etc.
    */
      const histogramCache: any = {}; /* maybe change this so that it computes ... */
      const summary =
        summaryContinuousCol(col); /* this is memoized, so it's free the second time you call it */
      const { min: domainMin, max: domainMax } = summary;
      const numBins = 40;
      const { TOP: topMargin, LEFT: leftMargin } = newMargin; /* changes with mini */

      histogramCache.domain = [domainMin, domainMax]; /* doesn't change with mini */

      histogramCache.x = d3
        .scaleLinear()
        .domain([domainMin, domainMax])
        .range([leftMargin, leftMargin + newWidth]);
      // trace 2

      histogramCache.bins = histogramContinuous(col, numBins, [domainMin, domainMax], null);

      histogramCache.binWidth = (domainMax - domainMin) / numBins;

      histogramCache.binStart = (i) => domainMin + i * histogramCache.binWidth;
      histogramCache.binEnd = (i) => domainMin + (i + 1) * histogramCache.binWidth;

      const yMax = histogramCache.bins.reduce((l, r) => (l > r ? l : r));

      histogramCache.y = d3
        .scaleLinear()
        .domain([0, yMax])
        .range([topMargin + newHeight, topMargin]);
      return histogramCache;
    },
    (col: DataCol, newMargin, newWidth, newHeight) => {
      const colId = col.getColId();
      return `${colId}-${newMargin}-${newWidth}-${newHeight}`;
    },
    50,
  );

  const fetchColumn = async () => {
    if (isObs) {
      const col = await cellSelectorAdata.getObsCol(field);
      return col;
    } else if (isGeneSetSummary) {
      const genesetName = field;
      const geneset = genesets[genesetName];
      const geneNames = geneset.genes.map((item) => {
        return item.name;
      });
      const colIndexes = await cellSelectorAdata.getIndexByVarNameList(geneNames);
      const cols = await cellSelectorAdata.getXCols(colIndexes);
      const meanCol = meanCols(cols);
      return meanCol;
    } else {
      const colIndexes = await cellSelectorAdata.getIndexByVarNameList([field]);
      const [col] = await cellSelectorAdata.getXCols(colIndexes);
      return col;
    }
  };

  const changeCellFilter = async (
    newRange: [number, number] | null,
    field: string,
    fetchColumn,
  ) => {
    if (newRange) {
      const currentRange = newRange;

      const col = await fetchColumn();
      if (!col) return;
      // const colorArray: string[] = colorKey as string[];

      cellSelectorFilter.setContinuousFilterCondition(field, col, currentRange);
    } else {
      cellSelectorFilter.removeContinuousFilterConditionsByKey(field);
    }
    cellSelectorFilter.upgradeVersionUuid();
    setCellFilterVersionUuid(cellSelectorFilter.getVersionUuid());
  };

  /* memoized closure to prevent HistogramHeader unecessary repaint */
  // const handleColorAction = (field: string, isObs: boolean) => {
  //   console.log('handleColorAction', field, isObs);
  // };

  const onBrush = (_: any, x) => {
    return () => {
      // ignore programmatically generated events
      if (!d3.event.sourceEvent) return;
      // ignore cascading events, which are programmatically generated
      if (d3.event.sourceEvent.sourceEvent) return;

      const range = d3.event.selection
        ? [x(d3.event.selection[0]), x(d3.event.selection[1])]
        : null;

      changeCellFilter(range as [number, number] | null, field, fetchColumn);
    };
  };

  const onBrushEnd = (_: any, x) => () => {
    const minAllowedBrushSize = 10;
    const smallAmountToAvoidInfiniteLoop = 0.1;
    // ignore programmatically generated events
    if (!d3.event.sourceEvent) return;
    // ignore cascading events, which are programmatically generated
    if (d3.event.sourceEvent.sourceEvent) return;

    let range: any = null;
    if (d3.event.selection) {
      if (d3.event.selection[1] - d3.event.selection[0] > minAllowedBrushSize) {
        range = [x(d3.event.selection[0]), x(d3.event.selection[1])];
      } else {
        const procedurallyResizedBrushWidth =
          d3.event.selection[0] + minAllowedBrushSize + smallAmountToAvoidInfiniteLoop; //

        range = [x(d3.event.selection[0]), x(procedurallyResizedBrushWidth)];
      }
    }

    // changeCellFilter(range as [number, number] | null);
    changeCellFilter(range as [number, number] | null, field, fetchColumn);
  };

  // const handleSetGeneAsScatterplotX = () => {
  //   console.log('handleSetGeneAsScatterplotX', field);
  // };

  // const handleSetGeneAsScatterplotY = () => {
  //   console.log('handleSetGeneAsScatterplotY', field);
  // };

  // const removeHistogram = () => {
  //   if (isColorAndMarkerAccessor) {
  //     console.log('removeHistogram--isColorAndMarkerAccessor', isColorAndMarkerAccessor);
  //   }
  //   if (isScatterplotXXaccessor) {
  //     console.log('removeHistogram--isScatterplotXXaccessor', isScatterplotXXaccessor);
  //   }
  //   if (isScatterplotYYaccessor) {
  //     console.log('removeHistogram--isScatterplotYYaccessor', isScatterplotYYaccessor);
  //   }
  // };

  const fetchAsyncProps = async () => {
    setLoading(true);
    setError(false);
    try {
      const column = await fetchColumn();
      // const colorArray: string[] = colorKey as string[];
      if (!column) {
        throw new Error('column is null');
      }
      const summary = summaryContinuousCol(column);
      const range = [summary.min, summary.max];
      // console.log('range', range);

      const unclippedRange = [...range];

      // if we are clipped, fetch both our value and our unclipped value,
      // as we need the absolute min/max range, not just the clipped min/max.

      const histogram = calcHistogramCache(column, MARGIN, width || WIDTH, HEIGHT);
      // trace 1
      const miniHistogram = calcHistogramCache(
        column,
        MARGIN_MINI,
        width || WIDTH_MINI,
        HEIGHT_MINI,
      );

      const isSingleValue = summary.min === summary.max;
      const nonFiniteExtent =
        summary.min === undefined ||
        summary.max === undefined ||
        Number.isNaN(summary.min) ||
        Number.isNaN(summary.max);

      const OK2Render = !nonFiniteExtent;

      setChartInfo({
        histogram,
        miniHistogram,
        range,
        unclippedRange,
        isSingleValue,
        OK2Render,
      });
    } catch (e) {
      setError(true);
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (containerRef.current) {
      setWidth(
        containerRef.current.clientWidth - 70 < 0
          ? containerRef.current.clientWidth
          : containerRef.current.clientWidth - 70,
      );
      fetchAsyncProps();
    }
  }, [containerRef.current, width, hideAnno, geneColorMode, colorKey]);

  useEffect(() => {
    windowListener.register('resize', `${field}-${isObs}-${mini}`, () => {
      if (containerRef.current) {
        setWidth(
          containerRef.current.clientWidth - 70 < 0
            ? containerRef.current.clientWidth
            : containerRef.current.clientWidth - 70,
        );
      }
    });
    return () => {
      windowListener.unregister('resize', `${field}-${isObs}-${mini}`);
    };
  }, []);

  const fieldForId = field.replace(/\s/g, '_');

  return (
    <div
      style={{
        width: '100%',
        height: mini ? HEIGHT_MINI : HEIGHT + 70,
      }}
      ref={containerRef}
    >
      {loading && (
        <div
          style={{
            height: mini ? HEIGHT_MINI : HEIGHT,
          }}
        >
          <StillLoading displayName={field} zebra={zebra} />
        </div>
      )}
      {error && <ErrorLoading zebra={zebra} displayName={field} />}
      {chartInfo.OK2Render && (
        <div
          id={`histogram_${fieldForId}`}
          style={{
            padding: mini ? 0 : '10px 12px',
            backgroundColor: zebra ? 'grey' : 'white',
          }}
        >
          <Histogram
            field={field}
            fieldForId={fieldForId}
            display={chartInfo.isSingleValue ? 'none' : 'block'}
            histogram={mini ? chartInfo.miniHistogram : chartInfo.histogram}
            width={width}
            height={mini ? HEIGHT_MINI : HEIGHT}
            onBrush={onBrush}
            onBrushEnd={onBrushEnd}
            margin={mini ? MARGIN_MINI : MARGIN}
            isColorBy={isColorAndMarkerAccessor}
            mini={mini}
            geneColorMode={geneColorMode}
            selectionRange={cellSelectorFilter.continuousColValueRangeMap.get(field)}
          />
          {!mini && (
            <HistogramFooter
              isGeneSetSummary={isGeneSetSummary}
              isObs={isObs}
              displayName={field}
              hideRanges={chartInfo.isSingleValue}
              rangeMin={chartInfo.unclippedRange[0]}
              rangeMax={chartInfo.unclippedRange[1]}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default BrushableHistogram;
