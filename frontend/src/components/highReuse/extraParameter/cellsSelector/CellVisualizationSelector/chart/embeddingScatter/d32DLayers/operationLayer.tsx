import { ChartOperationMode } from '@/constants/cellSelector';
import type { SelectionPolygon } from '@/interfaces/scatter';
import * as d3 from 'd3';
import { useEffect, useRef } from 'react';

type OperationLayerProps = {
  chartSize: {
    width: number;
    height: number;
  };
  setTransform: (transform: d3.ZoomTransform) => void;
  scales: null | {
    xScale: d3.ScaleLinear<number, number>;
    yScale: d3.ScaleLinear<number, number>;
  };
  selectionPolygon: SelectionPolygon;
  updateSelectionPolygon: (polygon: [number, number][] | null) => void;
  transform: d3.ZoomTransform;
  chartOperationMode: string;
  setLegendLayout: (offset: { left: number; top: number; width: number; height: number }) => void;
  legendLayout: {
    left: number;
    top: number;
    width: number;
    height: number;
  };
  isShowBorder: boolean;
};

export const OperationLayer = (props: OperationLayerProps) => {
  const {
    chartSize,
    setTransform,
    scales,
    selectionPolygon,
    updateSelectionPolygon,
    transform,
    chartOperationMode,
    legendLayout,
    isShowBorder,
  } = props;

  const operationLayerRef = useRef(null as null | HTMLCanvasElement);

  // const lassoPointsRef = useRef(null as null | [number, number][]);

  // const legendDraggedInnerOffset = useRef(null as null | { x: number; y: number });

  const isZoomingRef = useRef(false);

  const legendLayoutRef = useRef(legendLayout);

  // const isValidLassoRef = useRef(false);

  // const isLassoingRef = useRef(false);

  const zoomRef = useRef(null);

  // Anchor Ref
  const anchorPointsRef = useRef(null as null | [number, number][]);

  const isValidAnchorRef = useRef(false);

  const isAnchoringRef = useRef(false);

  // const checkIsInLegend = (x: number, y: number) => {
  //   const { left, top, width, height } = legendLayoutRef.current as {
  //     left: number;
  //     top: number;
  //     width: number;
  //     height: number;
  //   };
  //   if (x >= left && x <= left + width && y >= top && y <= top + height) {
  //     return true;
  //   }
  //   return false;
  // };

  const drawAnchor = (polygon: [number, number][] | null) => {
    const canvas = operationLayerRef.current as HTMLCanvasElement;
    const context = canvas.getContext('2d') as CanvasRenderingContext2D;
    // Clear the canvas
    context.clearRect(0, 0, chartSize.width, chartSize.height);
    if (!polygon || !scales) {
      return;
    }

    context.save();
    context.translate(transform.x, transform.y);
    context.scale(transform.k, transform.k);
    const { xScale, yScale } = scales;
    context.setLineDash([3, 3]);
    context.beginPath();

    // Draw anchor points
    polygon.forEach((point, index) => {
      const [x, y] = point;
      const [xPixel, yPixel] = [xScale(x), yScale(y)];

      // If this is not the first point, draw the connecting line
      if (index === 0) {
        context.moveTo(xPixel, yPixel);
      } else {
        context.lineTo(xPixel, yPixel);
      }
    });
    context.closePath();

    context.strokeStyle = isValidAnchorRef.current
      ? 'rgba(64, 255, 200, 0.3)'
      : 'rgba(64, 204, 248, 0.3)';

    context.lineWidth = 2;

    context.stroke();

    context.fillStyle = isValidAnchorRef.current
      ? 'rgba(64, 255, 200, 0.1)'
      : 'rgba(64, 204, 248, 0.1)';

    context.fill();

    // Draw points
    polygon.forEach((point, index) => {
      const [x, y] = point;
      const [xPixel, yPixel] = [xScale(x), yScale(y)];

      context.beginPath(); // Start a new path for each point
      context.setLineDash([]);
      context.arc(xPixel, yPixel, 3, 0, Math.PI * 2, true);
      if (index === 0) {
        context.strokeStyle = 'black'; // The first point is hollow
        context.stroke();
      } else {
        context.fillStyle = 'black'; // Other points are filled
        context.fill();
      }
    });

    context.restore();
  };

  const handleMouseMove = (event: MouseEvent) => {
    if (!scales || !anchorPointsRef.current) {
      return;
    }

    const { xScale, yScale } = scales;
    const { transform } = props;

    const x = event.layerX;
    const y = event.layerY;

    // Use the scales and transform to convert screen coordinates to a point in data coordinates
    const transformedXScale = transform.rescaleX(xScale);
    const transformedYScale = transform.rescaleY(yScale);
    const scaledX = transformedXScale.invert(x);
    const scaledY = transformedYScale.invert(y);

    // Update the coordinates of the last point
    anchorPointsRef.current[anchorPointsRef.current.length - 1] = [scaledX, scaledY];

    // Clear the canvas and redraw the polygon
    const canvas = operationLayerRef.current as HTMLCanvasElement;
    const context = canvas.getContext('2d') as CanvasRenderingContext2D;
    context.clearRect(0, 0, chartSize.width, chartSize.height);
    drawAnchor(anchorPointsRef.current);
    if (!isAnchoringRef.current) {
      document.removeEventListener('mousemove', handleMouseMove);
    }
  };

  const handleCanvasMouseUp = () => {
    // Remove the mouse-move event listener
    document.removeEventListener('mousemove', handleMouseMove);
    // ...
  };

  const handleCanvasMouseClick = (event: any) => {
    if (!scales) {
      return;
    }

    const canvas = operationLayerRef.current;
    if (!canvas) {
      return;
    }

    // If the polygon is already valid, stop listening for mouse-move events
    if (isValidAnchorRef.current) {
      anchorPointsRef.current = null;
      isValidAnchorRef.current = false;
      updateSelectionPolygon(anchorPointsRef.current);
      drawAnchor(anchorPointsRef.current);
      return;
    }

    const x = event.layerX;
    const y = event.layerY;

    // Use the scales and transform to convert screen coordinates to a point in data coordinates
    const { xScale, yScale } = scales;
    const { transform } = props;
    const transformedXScale = transform.rescaleX(xScale);
    const transformedYScale = transform.rescaleY(yScale);
    const scaledX = transformedXScale.invert(x);
    const scaledY = transformedYScale.invert(y);
    // Add the new point to anchorPointsRef
    anchorPointsRef.current = [...(anchorPointsRef.current || []), [scaledX, scaledY]];
    // if (anchorPointsRef.current.length == 1) {
    //   anchorPointsRef.current = [...anchorPointsRef.current, [scaledX, scaledY]];
    // }
    isAnchoringRef.current = true;
    // Draw the first point
    document.addEventListener('mousemove', handleMouseMove);

    if (anchorPointsRef.current.length > 2) {
      const endPoint = anchorPointsRef.current.at(-1);
      const startPoint = anchorPointsRef.current.at(0);

      const distanceBetweenStartAndEnd = Math.sqrt(
        (endPoint[1] - startPoint[1]) ** 2 + (endPoint[0] - startPoint[0]) ** 2,
      );
      const transformedDistance =
        transformedXScale(distanceBetweenStartAndEnd) - transformedXScale(0);
      if (transformedDistance > 10) {
        isValidAnchorRef.current = false;
        isAnchoringRef.current = true;
      } else {
        isValidAnchorRef.current = true;
        isAnchoringRef.current = false;
      }
    }

    if (isValidAnchorRef.current) {
      updateSelectionPolygon(anchorPointsRef.current);
    }
    drawAnchor(anchorPointsRef.current);
  };

  const handleCanvasMouseClickByRight = (event: any) => {
    // Check for a right mouse click
    if (event.button === 2) {
      // Right click: clear the anchor points
      anchorPointsRef.current = null;
      isValidAnchorRef.current = false;
      isAnchoringRef.current = false;
      updateSelectionPolygon(anchorPointsRef.current);
      drawAnchor(anchorPointsRef.current);
      return;
    }

    // Handle left-click logic
    if (!scales) {
      return;
    }
    const canvas = operationLayerRef.current;
    if (!canvas) {
      return;
    }

    // If the polygon is already valid, stop listening for mouse-move events
    if (isValidAnchorRef.current) {
      anchorPointsRef.current = null;
      isValidAnchorRef.current = false;
      updateSelectionPolygon(anchorPointsRef.current);
      drawAnchor(anchorPointsRef.current);
      return;
    }

    const x = event.layerX;
    const y = event.layerY;

    // Use the scales and transform to convert screen coordinates to a point in data coordinates
    const { xScale, yScale } = scales;
    const { transform } = props;
    const transformedXScale = transform.rescaleX(xScale);
    const transformedYScale = transform.rescaleY(yScale);
    const scaledX = transformedXScale.invert(x);
    const scaledY = transformedYScale.invert(y);

    // Add the new point to anchorPointsRef
    anchorPointsRef.current = [...(anchorPointsRef.current || []), [scaledX, scaledY]];
    isAnchoringRef.current = true;

    if (anchorPointsRef.current.length > 2) {
      const endPoint = anchorPointsRef.current.at(-1);
      const startPoint = anchorPointsRef.current.at(0);
      const distanceBetweenStartAndEnd = Math.sqrt(
        (endPoint[1] - startPoint[1]) ** 2 + (endPoint[0] - startPoint[0]) ** 2,
      );
      const transformedDistance =
        transformedXScale(distanceBetweenStartAndEnd) - transformedXScale(0);
      if (transformedDistance > 10) {
        isValidAnchorRef.current = false;
        isAnchoringRef.current = true;
      } else {
        isValidAnchorRef.current = true;
        isAnchoringRef.current = false;
      }
    }

    if (isValidAnchorRef.current) {
      updateSelectionPolygon(anchorPointsRef.current);
    }
    drawAnchor(anchorPointsRef.current);
  };
  // const drawLasso = (polygon: [number, number][] | null) => {
  //   const canvas = operationLayerRef.current as HTMLCanvasElement;
  //   const context = canvas.getContext('2d') as CanvasRenderingContext2D;
  //   // Draw the lasso path
  //   context.clearRect(0, 0, chartSize.width, chartSize.height);
  //   if (!polygon || polygon.length < 6 || !scales) {
  //     return;
  //   }

  //   context.save();

  //   context.translate(transform.x, transform.y);
  //   context.scale(transform.k, transform.k);

  //   const { xScale, yScale } = scales;

  //   context.setLineDash([3, 3]);

  //   context.beginPath();

  //   polygon.forEach((point, index) => {
  //     const [x, y] = point;
  //     const [xPixel, yPixel] = [xScale(x), yScale(y)];
  //     if (index === 0) {
  //       context.moveTo(xPixel, yPixel);
  //     } else {
  //       context.lineTo(xPixel, yPixel);
  //     }
  //   });
  //   context.closePath();

  //   context.strokeStyle = isValidLassoRef.current
  //     ? 'rgba(64, 255, 200, 0.3)'
  //     : 'rgba(64, 204, 248, 0.3)';

  //   context.lineWidth = 2;

  //   context.stroke();

  //   context.fillStyle = isValidLassoRef.current
  //     ? 'rgba(64, 255, 200, 0.1)'
  //     : 'rgba(64, 204, 248, 0.1)';

  //   context.fill();

  //   context.restore();
  // };

  // const handleMouseMoveWithDraggingLegend = () => {
  //   const canvas = operationLayerRef.current;
  //   if (!canvas) {
  //     return;
  //   }
  //   // const x = event.layerX;
  //   // const y = event.layerY;
  //   // const { x: draggedX, y: draggedY } = legendDraggedInnerOffset.current as {
  //   //   x: number;
  //   //   y: number;
  //   // };
  //   // setLegendLayout({
  //   //   ...legendLayout,
  //   //   left: x - draggedX,
  //   //   top: y - draggedY,
  //   //   // width: legendLayoutRef.current.width,
  //   //   // height: legendLayoutRef.current.height,
  //   // });
  // };

  // const handleMouseMoveWithLasso = (event: any) => {
  //   if (!scales) {
  //     return;
  //   }
  //   const x = event.layerX;
  //   const y = event.layerY;

  //   const { xScale, yScale } = scales;

  //   const { transform } = props;

  //   const transformedXScale = transform.rescaleX(xScale);

  //   const transformedYScale = transform.rescaleY(yScale);

  //   lassoPointsRef.current = [
  //     ...(lassoPointsRef.current || []),
  //     [transformedXScale.invert(x), transformedYScale.invert(y)],
  //   ];

  //   if (lassoPointsRef.current.length > 2) {
  //     const endPoint = lassoPointsRef.current.at(-1);
  //     const startPoint = lassoPointsRef.current.at(0);
  //     const distanceBetweenStartAndEnd = Math.sqrt(
  //       (endPoint[1] - startPoint[1]) ** 2 + (endPoint[0] - startPoint[0]) ** 2,
  //     );
  //     const transformedDistance =
  //       transformedXScale(distanceBetweenStartAndEnd) - transformedXScale(0);
  //     if (transformedDistance > 100) {
  //       isValidLassoRef.current = false;
  //     } else {
  //       isValidLassoRef.current = true;
  //     }
  //   }

  //   drawLasso(lassoPointsRef.current);
  // };

  // const handleCanvasMouseMove = (event: any) => {
  //   if (legendDraggedInnerOffset.current) {
  //     handleMouseMoveWithDraggingLegend(event);
  //   } else if (isLassoingRef.current) {
  //     handleMouseMoveWithLasso(event);
  //   }
  // };

  // const handleCanvasMouseUp = async () => {
  //   if (!scales) {
  //     return;
  //   }

  //   const canvas = operationLayerRef.current;
  //   if (!canvas) {
  //     return;
  //   }
  //   if (!!legendDraggedInnerOffset.current) {
  //     legendDraggedInnerOffset.current = null;
  //     return;
  //   }
  //   if (!!isLassoingRef.current) {
  //     isLassoingRef.current = false;
  //     if (!lassoPointsRef.current || lassoPointsRef.current.length < 6) {
  //       lassoPointsRef.current = null;
  //     } else {
  //       if (!isValidLassoRef.current) {
  //         lassoPointsRef.current = null;
  //       }
  //     }
  //     updateSelectionPolygon(lassoPointsRef.current);
  //     drawLasso(lassoPointsRef.current);
  //   }
  // };

  // const handleCanvasMouseDown = (event: any) => {
  //   if (!scales) {
  //     return;
  //   }
  //   const canvas = operationLayerRef.current;
  //   if (!canvas) {
  //     return;
  //   }
  //   const x = event.layerX;
  //   const y = event.layerY;

  //   if (checkIsInLegend(x, y)) {
  //     legendDraggedInnerOffset.current = {
  //       x: x - legendLayoutRef.current.left,
  //       y: y - legendLayoutRef.current.top,
  //     };
  //   } else {
  //     const { xScale, yScale } = scales;
  //     const { transform } = props;
  //     const transformedXScale = transform.rescaleX(xScale);
  //     const transformedYScale = transform.rescaleY(yScale);
  //     lassoPointsRef.current = [[transformedXScale.invert(x), transformedYScale.invert(y)]];
  //     isLassoingRef.current = true;
  //     isValidLassoRef.current = false;
  //   }
  // };

  // useEffect(() => {
  //   drawLasso(!!selectionPolygon ? selectionPolygon.getPointArray() : null);
  // }, [chartSize, selectionPolygon, scales, transform]);

  useEffect(() => {
    drawAnchor(!!selectionPolygon ? selectionPolygon.getPointArray() : null);
  }, [chartSize, selectionPolygon, scales, transform]);

  const handleZoomStart = () => {
    // const event = d3.event;
    // console.log(event);

    // const sourceEvent = event.sourceEvent;
    // const { layerX, layerY } = sourceEvent;
    // console.log(checkIsInLegend(layerX, layerY));

    // if (checkIsInLegend(layerX, layerY)) {
    //   legendDraggedInnerOffset.current = {
    //     x: layerX - legendLayoutRef.current.left,
    //     y: layerY - legendLayoutRef.current.top,
    //   };
    //   console.log('legendDraggedInnerOffset', legendDraggedInnerOffset);
    // } else {
    isZoomingRef.current = true;
    // }
  };

  const handleZoomed = () => {
    // if (!!legendDraggedInnerOffset.current) {
    // const { layerX: x, layerY: y } = d3.event.sourceEvent;
    // const { x: draggedX, y: draggedY } = legendDraggedInnerOffset.current as {
    //   x: number;
    //   y: number;
    // };
    // setLegendLayout({
    //   ...legendLayout,
    //   left: x - draggedX,
    //   top: y - draggedY,
    //   // width: legendLayoutRef.current.width,
    //   // height: legendLayoutRef.current.height,
    // });
    // } else
    if (isZoomingRef.current) {
      const newTransform = d3.event.transform;
      setTransform(newTransform);
    }
  };

  const handleZoomEnd = () => {
    // if (!!legendDraggedInnerOffset.current) {
    //   legendDraggedInnerOffset.current = null;
    //   const newTransform = d3.zoomIdentity.translate(transform.x, transform.y).scale(transform.k);
    //   d3.select(operationLayerRef.current).call(zoomRef.current.transform, newTransform);
    // } else
    if (isZoomingRef.current) {
      isZoomingRef.current = false;
    }
  };

  const cancelListener = () => {
    const operationLayer = operationLayerRef.current;
    if (!operationLayer) {
      return;
    }
    operationLayer.onclick = null;

    // operationLayer.onmousedown = null;
    // operationLayer.onmousemove = null;
    // operationLayer.onmouseup = null;
    d3.select(operationLayer).on('.zoom', null);
  };

  useEffect(() => {
    const operationLayer = operationLayerRef.current;
    if (!operationLayer) {
      return;
    }
    cancelListener();
    if (chartOperationMode === ChartOperationMode.BRUSH) {
      operationLayer.onclick = (e) => {
        handleCanvasMouseClick(e);
      };
      // Add the right-click event listener
      operationLayer.oncontextmenu = (event) => {
        event.preventDefault(); // Prevent the default context menu from appearing
        handleCanvasMouseClickByRight(event);
      };
      operationLayer.onmouseup = () => {
        handleCanvasMouseUp();
      };
    } else if (chartOperationMode === ChartOperationMode.DRAG) {
      const zoom = d3.zoom().scaleExtent([0.01, 100]);
      zoom.on('start', handleZoomStart);
      zoom.on('zoom', handleZoomed);
      zoom.on('end', handleZoomEnd);
      d3.select(operationLayer).call(zoom);
      zoomRef.current = zoom;
    }
  }, [chartOperationMode]);

  useEffect(() => {
    legendLayoutRef.current = legendLayout;
  }, [legendLayout]);

  return (
    <canvas
      ref={operationLayerRef}
      width={chartSize.width}
      height={chartSize.height}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        zIndex: 99,
        border: isShowBorder ? '2px solid black' : '0px',
      }}
    />
  );
};
