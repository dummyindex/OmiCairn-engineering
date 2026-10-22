import type { DataCol } from '@/interfaces/col';
import { message } from 'antd';
import type * as d3 from 'd3';
import { useEffect, useRef } from 'react';

const ANNOTATED_COLOR = '#aaa';
const DEFAULT_COLOR = 'rgba(0,0,0,0.5)';
const DEFAULT_SIZE = 2;
const MASKED_SIZE = 0;
const HIGHLIGHTED_SIZE = 8;

export type PointsLayerProps = {
  scaledXyCols: null | [DataCol, DataCol];
  sizeJudge: {
    highlightedTable: boolean[] | null;
    isMaskedFn: (index: number) => boolean;
  };
  colorJudge: {
    annotatedTable: boolean[] | null;
    colorTable: DataCol | null;
  };
  scales: null | {
    xScale: d3.ScaleLinear<number, number>;
    yScale: d3.ScaleLinear<number, number>;
  };
  freeze: boolean;
  chartSize: {
    width: number;
    height: number;
  };
  transform: d3.ZoomTransform;
  componentSize: number;
};

export const PointsLayer = (props: PointsLayerProps) => {
  const {
    scaledXyCols,
    colorJudge: { colorTable, annotatedTable },
    sizeJudge: { isMaskedFn, highlightedTable },
    scales,
    freeze,
    chartSize,
    transform,
    componentSize,
  } = props;

  const pointsLayerRef = useRef(null as null | HTMLCanvasElement);

  const renderPoints = async () => {
    if (freeze) {
      return;
    }
    if (!chartSize || !scaledXyCols || !scales) {
      return;
    }
    const [scaledXCol, scaledYCol] = scaledXyCols;
    try {
      const canvas = pointsLayerRef.current;
      if (!canvas) return;
      const context = canvas.getContext('2d');

      if (!context) {
        throw new Error('context is null');
      }
      // Clear the canvas
      context.clearRect(0, 0, chartSize.width, chartSize.height);
      context.save();
      context.translate(transform.x, transform.y);
      context.scale(transform.k, transform.k);

      // Draw the scatter points
      const WHOLE_CIRCLE = 2 * Math.PI;
      scaledXCol.forEach((xValue: number, index: number) => {
        // const x = scales.xScale(xValue);
        // const y = scales.yScale(yCol.at(index));
        const x = xValue;
        const y = scaledYCol.at(index);
        const color = annotatedTable?.at(index)
          ? ANNOTATED_COLOR
          : colorTable?.at(index) || DEFAULT_COLOR;
        const size = isMaskedFn(index)
          ? MASKED_SIZE
          : highlightedTable?.at(index)
          ? HIGHLIGHTED_SIZE
          : DEFAULT_SIZE;

        context.beginPath();
        context.arc(x, y, size * componentSize, 0, WHOLE_CIRCLE);
        context.closePath();
        context.fillStyle = color;
        context.fill();
      });
      context.restore();
    } catch (e) {
      console.log(e);
      message.error('Failed to load embedding data.');
    }
  };

  useEffect(() => {
    renderPoints();
  }, [
    scaledXyCols,
    colorTable,
    highlightedTable,
    isMaskedFn,
    scales,
    freeze,
    chartSize,
    transform,
  ]);

  return (
    <canvas
      ref={pointsLayerRef}
      width={chartSize.width}
      height={chartSize.height}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        zIndex: 0,
      }}
    />
  );
};
