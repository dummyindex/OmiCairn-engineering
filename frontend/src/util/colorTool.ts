import { DataCol } from '@/interfaces/col';
import chroma from 'chroma-js';
import * as d3 from 'd3';
import { memoize } from './fnTool';
import { normalizeContinuousCol } from './normalized';

export const mixColors = (colors: any[]) => {
  const handledColors = colors.map((color) => {
    if (color instanceof Array) {
      return color;
    } else if (typeof color === 'string') {
      return chroma(color).rgba();
    } else {
      const { r, g, b, a } = color;
      return [r, g, b, a];
    }
  });
  let resultRed = 0;
  let resultGreen = 0;
  let resultBlue = 0;
  let resultAlpha = 0;

  for (const [r, g, b, a] of handledColors) {
    resultRed += r * a;
    resultGreen += g * a;
    resultBlue += b * a;
    resultAlpha += a;
  }

  resultRed = resultAlpha > 0 ? resultRed / resultAlpha : 0;
  resultGreen = resultAlpha > 0 ? resultGreen / resultAlpha : 0;
  resultBlue = resultAlpha > 0 ? resultBlue / resultAlpha : 0;
  resultAlpha /= handledColors.length;

  return [resultRed, resultGreen, resultBlue, resultAlpha];
};

export const combineColorToAlphaCol = memoize(
  (color: [number, number, number], alphaCol: DataCol) => {
    const normalizedCol = normalizeContinuousCol(alphaCol);

    return normalizedCol.map((alpha: number) => {
      return `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${alpha})`;
    });
  },
  (color: [number, number, number], alphaCol: DataCol) => {
    return JSON.stringify(color) + alphaCol.getColId();
  },
  50,
);

export const mixColorCols: (colorCols: DataCol[]) => DataCol = memoize(
  (colorCols: DataCol[]) => {
    if (colorCols.length === 0) {
      return new DataCol();
    }
    const firstColorCol = colorCols.at(0);

    const mixedColorCol = firstColorCol.map((_, index) => {
      const colors = colorCols.map((col) => col.at(index));
      const mixedColor = mixColors(colors);
      return `rgba(${mixedColor[0]}, ${mixedColor[1]}, ${mixedColor[2]}, ${mixedColor[3]})`;
    });
    return mixedColorCol;
  },
  (colorCols: DataCol[]) => {
    const colIds = colorCols.map((col) => col.getColId());
    colIds.sort();
    return colIds.join(',');
  },
  50,
);

export const scaleGradientColorCol = (
  minV: number,
  maxV: number,
  colorCol: DataCol,
  geneColorMode: (index: number) => string,
): DataCol => {
  const colorScale = d3.scaleSequential(geneColorMode).domain([maxV, minV]);

  const gradientColorCol = colorCol.map((value: number) => {
    return colorScale(value);
  });
  return gradientColorCol;
};
