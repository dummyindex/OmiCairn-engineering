import type { SelectionPolygon } from '@/interfaces/scatter';
import { memoize } from './fnTool';
import type { DataCol } from '@/interfaces/col';
import * as d3 from 'd3';

export const judgePointsInPolygon = (points: number[][], selectionRange: SelectionPolygon) => {
  const polygon = selectionRange.getPointArray();
  const result: boolean[] = new Array(points.length);
  for (let i = 0; i < points.length; i++) {
    const point = points[i];
    let inside = false;
    for (let j = 0, k = polygon.length - 1; j < polygon.length; k = j++) {
      const xi = polygon[j][0],
        yi = polygon[j][1];
      const xj = polygon[k][0],
        yj = polygon[k][1];
      const intersect =
        yi > point[1] != yj > point[1] && point[0] < ((xj - xi) * (point[1] - yi)) / (yj - yi) + xi;
      if (intersect) inside = !inside;
    }
    result[i] = inside;
  }
  return result;
};

const _judgeOnePointInPolygon = (ptx: number, pty: number, selectionRange: SelectionPolygon) => {
  const polygon = selectionRange.getPointArray();
  let inside = false;
  for (let j = 0, k = polygon.length - 1; j < polygon.length; k = j++) {
    const xi = polygon[j][0],
      yi = polygon[j][1];
    const xj = polygon[k][0],
      yj = polygon[k][1];
    const intersect = yi > pty != yj > pty && ptx < ((xj - xi) * (pty - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
};

export const judgeOnePointInPolygon = memoize(
  _judgeOnePointInPolygon,
  (x: number, y: number, selectionRange: SelectionPolygon) => {
    return `${x},${y},${selectionRange.getUniqueKey()}`;
  },
  10000,
);

export const computeBrushedFlagTable: (
  xCol: DataCol,
  yCol: DataCol,
  selectionRange: SelectionPolygon,
) => DataCol = memoize(
  (xCol: DataCol, yCol: DataCol, selectionRange: SelectionPolygon) => {
    const result = xCol.map((x: number, index: number) => {
      const point = [x, yCol.at(index)];
      const polygon = selectionRange.getPointArray();
      return d3.polygonContains(polygon, point);
    });
    return result;
  },
  (xCol: DataCol, yCol: DataCol, selectionRange: SelectionPolygon) => {
    return `${xCol.getColId()},${yCol.getColId()},${selectionRange.getUniqueKey()}`;
  },
  2,
);

export const computeCentreLabels = memoize(
  (xCol: DataCol, yCol: DataCol, clusterCol: DataCol) => {
    const { xyMap, countMap } = clusterCol?.reduce(
      (previous, label, index) => {
        const {
          xyMap: previousXyMap,
          countMap: previousCountMap,
        }: Record<string, Map<string, any>> = previous;
        if (previousXyMap.has(label)) {
          const previousXy = previousXyMap.get(label);
          previousXy[0] += xCol.at(index);
          previousXy[1] += yCol.at(index);
          previousXyMap.set(label, previousXy);
          previousCountMap.set(label, previousCountMap.get(label) + 1);
        } else {
          previousXyMap.set(label, [xCol.at(index), yCol.at(index)]);
          previousCountMap.set(label, 1);
        }
        return {
          xyMap: previousXyMap,
          countMap: previousCountMap,
        };
      },
      { xyMap: new Map(), countMap: new Map() },
    );
    const labelList = Array.from(xyMap.keys()).map((label) => {
      const [x, y] = xyMap.get(label);
      const count = countMap.get(label);
      return [x / count, y / count, label];
    });
    return labelList;
  },
  (xCol: DataCol, yCol: DataCol, clusterCol: DataCol) => {
    return `${xCol.getColId()},${yCol.getColId()},${clusterCol.getColId()}`;
  },
  10,
);
