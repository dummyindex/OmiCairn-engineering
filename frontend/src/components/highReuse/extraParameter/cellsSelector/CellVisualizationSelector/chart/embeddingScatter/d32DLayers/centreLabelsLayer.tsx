import type * as d3 from 'd3';
import { useEffect, useRef } from 'react';

type CentreLabelsLayerProps = {
  chartSize: {
    width: number;
    height: number;
  };
  scales: null | {
    xScale: d3.ScaleLinear<number, number>;
    yScale: d3.ScaleLinear<number, number>;
  };
  enable: boolean;
  labelPointList: [number, number, string][];
  transform: d3.ZoomTransform;
  fontSize: number;
  fontColor: string;
  fontFamily: string;
};

export const CentreLabelsLayer = (props: CentreLabelsLayerProps) => {
  const { chartSize, scales, enable, labelPointList, transform, fontSize, fontColor, fontFamily } =
    props;

  const centreLabelsLayerRef = useRef(null as null | HTMLCanvasElement);

  const drawCentreLabels = async () => {
    const canvas = centreLabelsLayerRef.current;
    if (!canvas) {
      return;
    }
    const context = canvas.getContext('2d');
    if (!context) {
      return;
    }
    context.clearRect(0, 0, chartSize.width, chartSize.height);

    if (!enable || !scales || !labelPointList) {
      return;
    }

    context.save();
    context.translate(transform.x, transform.y);
    context.scale(transform.k, transform.k);

    labelPointList.forEach(([x, y, label]: [number, number, string]) => {
      const { xScale, yScale } = scales;
      const xInChart = xScale(x);
      const yInChart = yScale(y);
      const labelWidth = context.measureText(label).width + 20;
      const labelHeight = 20;
      context.fillStyle = 'rgba(255, 255, 255, 0.6)';
      context.fillRect(
        xInChart - labelWidth / 2,
        yInChart - labelHeight / 2 - 3,
        labelWidth,
        labelHeight,
      );

      context.font = `${fontSize}px ${fontFamily}`;
      context.fillStyle = fontColor;
      context.textAlign = 'center';
      context.fillText(label, xInChart, yInChart);
    });

    context.restore();
  };

  useEffect(() => {
    drawCentreLabels();
  }, [chartSize, enable, scales, labelPointList, transform, fontSize, fontColor, fontFamily]);

  return (
    <canvas
      ref={centreLabelsLayerRef}
      width={chartSize.width}
      height={chartSize.height}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        zIndex: 1,
      }}
    />
  );
};
