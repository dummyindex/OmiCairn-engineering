import { ColorMode } from '@/constants/cellSelector';
// import type { DataCol } from '@/interfaces/col';
import { cellSelectorAdata } from '@/util/anndata';
import { cellSelectorFilter } from '@/util/cellFilter';
import { meanCols } from '@/util/colTool';
import * as d3 from 'd3';
import { useEffect, useRef, useState } from 'react';
import { useModel } from 'umi';

type CentreLabelsLayerProps = {
  chartSize: {
    width: number;
    height: number;
  };
  scales: null | {
    xScale: d3.ScaleLinear<number, number>;
    yScale: d3.ScaleLinear<number, number>;
  };
  legendData: [];
  legendLayout: {
    width: number;
    height: number;
    left: number;
    top: number;
  };
  chartOptions: any;
};

export const LegendLayer = (props: CentreLabelsLayerProps) => {
  const { chartSize, scales, legendData, legendLayout, chartOptions } = props;

  const { colorMode, setCellFilterVersionUuid, colorKey, genesets, geneColorMode } =
    useModel('cellSelect');
  const colorBarRange = useRef(null as null | any);
  const fetchGenesetColumn = async () => {
    const geneset = genesets[colorKey as string];
    const geneList = geneset.genes.map((item) => {
      return item.name;
    });
    const colIndexes = await cellSelectorAdata.getIndexByVarNameList(geneList);
    const cols = await cellSelectorAdata.getXCols(colIndexes);
    const meanCol = meanCols(cols);
    return meanCol;
  };

  const fetchGeneColumn = async () => {
    const colIndexes = await cellSelectorAdata.getIndexByVarNameList([colorKey] as string[]);
    const cols = await cellSelectorAdata.getXCols(colIndexes);

    const meanCol = meanCols(cols);
    return meanCol;
  };

  const fetchObsGeneColumn = async (field: string) => {
    const colIndexes = await cellSelectorAdata.getIndexByVarNameList([field]);
    const cols = await cellSelectorAdata.getXCols(colIndexes);

    const meanCol = meanCols(cols);
    return meanCol;
  };

  const fetchColumn = async (field: any) => {
    const col = await cellSelectorAdata.getObsCol(field);
    return col;
  };

  const changeCellFilterByGene = async (newRange: [number, number] | null, field: any) => {
    if (colorMode === ColorMode.CONTINUOUS_OBS_MULTIPLE) {
      if (newRange && colorKey) {
        const col = await fetchColumn(field);
        cellSelectorFilter.setContinuousFilterCondition(field, col, newRange);
      } else {
        cellSelectorFilter.removeContinuousFilterConditionsByKey(field);
      }
    } else if (colorMode === ColorMode.CONTINUOUS_XCOL) {
      if (newRange && colorKey) {
        const col = await fetchGeneColumn();
        if (!col) return;

        cellSelectorFilter.setContinuousFilterCondition(field, col, newRange);
      } else {
        cellSelectorFilter.removeContinuousFilterConditionsByKey(field);
      }
    } else if (colorMode === ColorMode.CONTINUOUS_X_COL_MULTIPLE && colorKey instanceof Array) {
      if (newRange && colorKey) {
        const col = await fetchObsGeneColumn(field);
        if (!col) return;

        cellSelectorFilter.setContinuousFilterCondition(field, col, newRange);
      } else {
        cellSelectorFilter.removeContinuousFilterConditionsByKey(field);
      }
    } else {
      if (newRange && colorKey) {
        const col = await fetchGenesetColumn();
        if (!col) return;
        cellSelectorFilter.setContinuousFilterCondition(colorKey, col, newRange);
      } else {
        cellSelectorFilter.removeContinuousFilterConditionsByKey(colorKey);
      }
    }
    cellSelectorFilter.upgradeVersionUuid();
    setCellFilterVersionUuid(cellSelectorFilter.getVersionUuid());
  };

  const changeCellFilterByObsContinuous = async (newRange: [number, number] | null, field: any) => {
    if (colorMode === ColorMode.CONTINUOUS_X_COL_AVG_MONOCHROME) {
      if (newRange && colorKey) {
        const col = await fetchGenesetColumn();
        if (!col) return;
        cellSelectorFilter.setContinuousFilterCondition(colorKey, col, newRange);
      } else {
        cellSelectorFilter.removeContinuousFilterConditionsByKey(colorKey);
      }
    } else if (colorMode === ColorMode.CONTINUOUS_XCOL_MONOCHROME) {
      if (newRange && colorKey) {
        const col = await fetchGeneColumn();
        if (!col) return;
        cellSelectorFilter.setContinuousFilterCondition(colorKey as string, col, newRange);
      } else {
        cellSelectorFilter.removeContinuousFilterConditionsByKey(field);
      }
    } else {
      if (newRange && colorKey) {
        const col = await fetchColumn(field);
        if (!col) return;

        cellSelectorFilter.setContinuousFilterCondition(field, col, newRange);
      } else {
        cellSelectorFilter.removeContinuousFilterConditionsByKey(field);
      }
    }
    cellSelectorFilter.upgradeVersionUuid();
    setCellFilterVersionUuid(cellSelectorFilter.getVersionUuid());
  };
  const [svgSize, setSetSvgSize] = useState({ width: 0, height: 0 });
  const {
    fontSize,
    fontColor,
    fontFamily,
    legendShape,
    LegendDirection,
    legendWidth,
    legendHeight,
    legendCol,
    legendTop,
    legendLeft,
    obsContinuousMode,
    colorBarWidth,
    colorBarDecimal,
    backgroundAlpha,
  } = chartOptions;
  const legendLayerRef = useRef(null);

  const drawLegend = async () => {
    if (!legendLayerRef.current) {
      return;
    }
    const svg = d3.select(legendLayerRef.current);
    if (legendData && legendData.length) {
      const newLegendHeight = Math.ceil(legendData.length / legendCol) * legendHeight;
      const lengthGroup = svg
        .select('.legend')
        .attr(
          'transform',
          LegendDirection === 'vertical'
            ? `translate(${0}, ${0})`
            : `rotate(90) translate(${0}, ${-newLegendHeight}) `,
        );

      lengthGroup.selectAll('*').remove();

      lengthGroup
        .append('rect')
        .attr('width', legendWidth * legendCol)
        .attr('height', newLegendHeight)
        .attr('fill', `rgba(255,255,255,${backgroundAlpha})`);

      const legendItems = lengthGroup
        .selectAll('.legend-item')
        .data(legendData)
        .enter()
        .append('g')
        .attr('class', 'legend-item')
        .attr('transform', (d, i) => {
          // Compute each legend item's position from the column count
          const row = Math.floor(i / legendCol);
          const col = i % legendCol;
          return `translate(${col * legendWidth}, ${row * legendHeight})`; // Adjust spacing and position as needed
        });

      legendItems
        .append('rect')
        .attr('width', 20)
        .attr('height', 20)
        .attr('rx', legendShape === 'square' ? 0 : 10)
        .attr('ry', legendShape === 'square' ? 0 : 10)
        .attr('fill', (d) => d.color);

      legendItems
        .append('foreignObject') // Use foreignObject to create a container holding the text
        .attr('x', 30)
        .attr('y', 0)
        .attr('width', legendWidth - 50) // Set the container width
        .attr('height', 25)
        .style('font-size', fontSize.legend)
        .style('color', fontColor.legend)
        .style('font-family', fontFamily.legend)
        .style('user-select', 'none')
        .text((d) => d.name);
    } else {
      const legend = svg.select('.legend');
      legend.selectAll('*').remove();
    }
  };

  const setupSliderByContinuous = (
    lengthGroup,
    legendData,
    index,
    colorBarDecimal,
    changeCellFilterByGene,
    xOffset,
    colorKey,
  ) => {
    let currentSliderMaxValue = cellSelectorFilter.continuousColValueRangeMap.get(colorKey)
      ? Math.max(
          cellSelectorFilter.continuousColValueRangeMap.get(colorKey)[0],
          cellSelectorFilter.continuousColValueRangeMap.get(colorKey)[1],
        )
      : legendData.max; // Current slider value

    let currentSliderMinValue = cellSelectorFilter.continuousColValueRangeMap.get(colorKey)
      ? Math.min(
          cellSelectorFilter.continuousColValueRangeMap.get(colorKey)[0],
          cellSelectorFilter.continuousColValueRangeMap.get(colorKey)[1],
        )
      : legendData.min; // Current slider value

    // Create the slider handle;
    lengthGroup
      .append('rect') // Use a rect to create a hollow handle
      .attr('class', `Max${index}`)
      .attr('x', -3 + xOffset) // Handle x coordinate
      .attr(
        'y',
        140 * (1 - (currentSliderMaxValue - legendData.min) / (legendData.max - legendData.min)),
      ) // Handle y coordinate
      .attr('width', 36)
      .attr('height', 5)
      .attr('rx', 2) // Set the horizontal corner radius
      .attr('ry', 2) // Set the vertical corner radius
      .style('fill', 'white') // Set the fill to white/transparent
      .style('stroke', '#5664B3') // Set the border color
      .style('stroke-width', 1) // Set the border width
      .style('cursor', 'pointer')
      .style('display', 'block');
    // Create the slider handle;
    lengthGroup
      .append('rect') // Use a rect to create a hollow handle
      .attr('class', `Min${index}`)
      .attr('x', -3 + xOffset) // Handle x coordinate
      .attr(
        'y',
        140 * (1 - (currentSliderMinValue - legendData.min) / (legendData.max - legendData.min)),
      ) // Handle y coordinate
      .attr('width', 36)
      .attr('height', 5)
      .attr('rx', 2) // Set the horizontal corner radius
      .attr('ry', 2) // Set the vertical corner radius
      .style('fill', 'white') // Set the fill to white/transparent
      .style('stroke', '#5664B3') // Set the border color
      .style('stroke-width', 1) // Set the border width
      .style('cursor', 'pointer')
      .style('display', 'block');
    // Get the slider handle DOM elements
    const sliderMax = lengthGroup.select(`.Max${index}`); // Adjust to match your selector
    const sliderMin = lengthGroup.select(`.Min${index}`); // Adjust to match your selector
    // Add a text element showing the value at the current position
    const sliderMaxValueText = lengthGroup
      .append('text')
      .attr('class', `slider-max${index}`)
      .attr('x', 40 + xOffset) // Adjust position
      .attr(
        'y',
        10 +
          140 * (1 - (currentSliderMaxValue - legendData.min) / (legendData.max - legendData.min)),
      ) // Adjust position
      .style('font-size', '12px') // Adjust font size
      .style('fill', 'black'); // Adjust font color
    // Add a text element showing the value at the current position
    const sliderMinValueText = lengthGroup
      .append('text')
      .attr('class', `slider-min${index}`)
      .attr('x', 40 + xOffset) // Adjust position
      .attr(
        'y',
        10 +
          140 * (1 - (currentSliderMinValue - legendData.min) / (legendData.max - legendData.min)),
      ) // Adjust position
      .style('font-size', '12px') // Adjust font size
      .style('fill', 'black'); // Adjust font color
    // Update the slider value text
    sliderMaxValueText.text(
      legendData.max ? currentSliderMaxValue.toFixed(colorBarDecimal) : legendData.max,
    );
    sliderMinValueText.text(
      legendData.max ? currentSliderMinValue.toFixed(colorBarDecimal) : `${legendData.min}`,
    );
    // Define the slider drag behavior
    const dragMax = d3.drag().on('drag', dragMaxHandler).on('end', dragEndMaxHandler);
    const dragMin = d3.drag().on('drag', dragHandlerMin).on('end', dragEndHandlerMin);
    // Apply the drag behavior to the slider handles
    sliderMax.call(dragMax);
    sliderMin.call(dragMin);
    // Drag event handler
    function dragMaxHandler() {
      // Get the slider position
      const newY = Math.min(140, Math.max(0, d3.event.y));
      sliderMax.attr('y', newY);
      sliderMaxValueText.attr('y', newY + 10);
      // Compute the corresponding value from the slider position
      const range = legendData.max - legendData.min;
      currentSliderMaxValue = legendData.min + (1 - newY / 140) * range;
      // Update the label below the slider handle
      lengthGroup.selectAll('.slider-max').text(currentSliderMaxValue.toFixed(colorBarDecimal));
      // sliderMax.style('fill', colorScale(currentSliderMinValue));
      // Update the slider value text
      sliderMaxValueText.text(currentSliderMaxValue.toFixed(colorBarDecimal));
      if (currentSliderMaxValue > currentSliderMinValue) {
        colorBarRange.current = [currentSliderMinValue, currentSliderMaxValue];
      } else {
        colorBarRange.current = [currentSliderMaxValue, currentSliderMinValue];
      }

      changeCellFilterByGene(colorBarRange.current, legendData.name);
    }
    // Drag-end event handler
    function dragEndMaxHandler() {
      // On drag end, clamp the slider value to the range
      currentSliderMaxValue = Math.max(
        legendData.min,
        Math.min(legendData.max, currentSliderMaxValue),
      );
      // Update the slider position from the new slider value
      const positionPercentage =
        (currentSliderMaxValue - legendData.min) / (legendData.max - legendData.min);
      const newY = 140 * (1 - positionPercentage);
      // Update the label below the slider handle
      lengthGroup.selectAll('.slider-max').text(currentSliderMaxValue.toFixed(colorBarDecimal));
      if (currentSliderMaxValue > currentSliderMinValue) {
        colorBarRange.current = [currentSliderMinValue, currentSliderMaxValue];
      } else {
        colorBarRange.current = [currentSliderMaxValue, currentSliderMinValue];
      }
      changeCellFilterByGene(colorBarRange.current, legendData.name);
      // Update the slider value text
      sliderMaxValueText.text(currentSliderMaxValue.toFixed(colorBarDecimal));
      // Update the slider position
      sliderMax.attr('y', newY);
      sliderMaxValueText.attr('y', newY + 10);
    }
    // Drag event handler for sliderMin
    function dragHandlerMin() {
      // Get the slider position
      const newY = Math.min(140, Math.max(0, d3.event.y));
      sliderMinValueText.attr('y', newY + 10);
      sliderMin.attr('y', newY);
      // Compute the corresponding value from the slider position
      const range = legendData.max - legendData.min;
      currentSliderMinValue = legendData.min + (1 - newY / 140) * range;
      // sliderMin.style('fill', colorScale(currentSliderMaxValue));
      sliderMinValueText.text(currentSliderMinValue.toFixed(colorBarDecimal));
      // Update the label below the slider handle
      lengthGroup.selectAll('.sliderMinValue').text(currentSliderMinValue.toFixed(colorBarDecimal));
      if (currentSliderMaxValue > currentSliderMinValue) {
        colorBarRange.current = [currentSliderMinValue, currentSliderMaxValue];
      } else {
        colorBarRange.current = [currentSliderMaxValue, currentSliderMinValue];
      }
      changeCellFilterByGene(colorBarRange.current, legendData.name);
    }
    // Drag-end event handler for sliderMin
    function dragEndHandlerMin() {
      // On drag end, clamp the slider value to the range
      currentSliderMinValue = Math.max(
        legendData.min,
        Math.min(legendData.max, currentSliderMinValue),
      );
      // Update the slider position from the new slider value
      const positionPercentage =
        (currentSliderMinValue - legendData.min) / (legendData.max - legendData.min);
      const newY = 140 * (1 - positionPercentage);
      // Update the slider value text
      lengthGroup.selectAll('.sliderMinValue').text(currentSliderMinValue.toFixed(colorBarDecimal));
      // Update the slider position
      sliderMin.attr('y', newY);
      sliderMinValueText.attr('y', newY + 10);
      if (currentSliderMaxValue > currentSliderMinValue) {
        colorBarRange.current = [currentSliderMinValue, currentSliderMaxValue];
      } else {
        colorBarRange.current = [currentSliderMaxValue, currentSliderMinValue];
      }
      changeCellFilterByGene(colorBarRange.current, legendData.name);
    }
  };

  const drawLegendByContinuous = async (legendData) => {
    if (!legendLayerRef.current) {
      return;
    }
    const svg = d3.select(legendLayerRef.current);
    const lengthGroup = svg
      .select('.legend')
      .attr(
        'transform',
        LegendDirection === 'vertical'
          ? `translate(${10}, ${0})`
          : `rotate(90) translate(${10}, ${-150})`,
      );

    lengthGroup.selectAll('*').remove();
    if (legendData && legendData.length > 0) {
      const legendWidth = colorBarWidth; // Height of each individual legend

      // Loop through each item in the legendData array
      legendData.forEach(async (item, index) => {
        const getColorArr = () => {
          const colorArr = [];

          if (!item.colorScale) {
            const colorScale = d3.scaleSequential(geneColorMode).domain([0, 1]);
            for (let i = 0; i < 1; i += 0.01) {
              colorArr.push(colorScale(i));
            }
          } else {
            for (let i = 0; i < 1; i += 0.01) {
              colorArr.push(item.colorScale(i));
            }
          }

          return colorArr;
        };

        const colorArr = getColorArr();
        const xOffset = index * legendWidth;
        const gradient = lengthGroup
          .append('defs')
          .append('linearGradient')
          .attr('id', `legendGradient_${index}`)
          .attr('x1', '0%')
          .attr('y1', '0%')
          .attr('x2', '0%')
          .attr('y2', '100%');

        colorArr.forEach((color, index) => {
          gradient
            .append('stop')
            .attr('offset', `${(index / (colorArr.length - 1)) * 100}%`) // Compute the offset from the array length
            .style('stop-color', color);
        });

        lengthGroup
          .append('rect')
          .attr('x', xOffset)
          .attr('y', 0)
          .attr('width', 30) // Width
          .attr('height', 145) // Height
          .style('fill', `url(#legendGradient_${index})`);
        // let currentSliderMaxValue = item.maxV; // Current slider value
        // let currentSliderMinValue = item.minV; // Current slider value

        // Add labels
        lengthGroup
          .append('text')
          .attr('x', 40 + xOffset) // Label x position
          .attr('y', 140) // Label y position
          .style('user-select', 'none')
          .style('font-size', fontSize.legend)
          .style('color', fontColor.legend)
          .style('font-family', fontFamily.legend)
          .text(item.min ? item.min.toFixed(colorBarDecimal) : item.min);

        lengthGroup
          .append('text')
          .attr('x', 40 + xOffset)
          .attr('y', 20)
          .style('user-select', 'none')
          .style('font-size', fontSize.legend)
          .style('color', fontColor.legend)
          .style('font-family', fontFamily.legend)
          .text(item.max ? item.max.toFixed(colorBarDecimal) : item.max);

        setupSliderByContinuous(
          lengthGroup,
          item,
          index,
          colorBarDecimal,
          changeCellFilterByGene,
          xOffset,
          item.name,
        );
      });
    }
  };

  // Single color
  const setupSliderByObsContinuous = async (data, index, lengthGroup, colorBarDecimal, xOffset) => {
    let currentSliderMaxValue = cellSelectorFilter.continuousColValueRangeMap.get(colorKey)
      ? Math.max(
          cellSelectorFilter.continuousColValueRangeMap.get(colorKey)[0],
          cellSelectorFilter.continuousColValueRangeMap.get(colorKey)[1],
        )
      : data.maxV; // Current slider value

    let currentSliderMinValue = cellSelectorFilter.continuousColValueRangeMap.get(colorKey)
      ? Math.min(
          cellSelectorFilter.continuousColValueRangeMap.get(colorKey)[0],
          cellSelectorFilter.continuousColValueRangeMap.get(colorKey)[1],
        )
      : data.minV;

    // Create the slider handle;
    lengthGroup
      .append('rect') // Use a rect to create a hollow handle
      .attr('class', `Max${index}`)
      .attr('x', -3 + xOffset) // Handle x coordinate
      .attr('y', 140 * (1 - (currentSliderMaxValue - data.minV) / (data.maxV - data.minV))) // Handle y coordinate
      .attr('width', 36)
      .attr('height', 5)
      .attr('rx', 2) // Set the horizontal corner radius
      .attr('ry', 2) // Set the vertical corner radius
      .style('fill', 'white') // Set the fill to white/transparent
      .style('stroke', '#5664B3') // Set the border color
      .style('stroke-width', 1) // Set the border width
      .style('cursor', 'pointer')
      .style('display', 'block');
    // Create the slider handle;
    lengthGroup
      .append('rect') // Use a rect to create a hollow handle
      .attr('class', `Min${index}`)
      .attr('x', -3 + xOffset) // Handle x coordinate
      .attr('y', 140 * (1 - (currentSliderMinValue - data.minV) / (data.maxV - data.minV))) // Handle y coordinate
      .attr('width', 36)
      .attr('height', 5)
      .attr('rx', 2) // Set the horizontal corner radius
      .attr('ry', 2) // Set the vertical corner radius
      .style('fill', 'white') // Set the fill to white/transparent
      .style('stroke', '#5664B3') // Set the border color
      .style('stroke-width', 1) // Set the border width
      .style('cursor', 'pointer')
      .style('display', 'block');

    // Get the slider handle DOM elements
    const sliderMax = lengthGroup.select(`.Max${index}`); // Adjust to match your selector
    const sliderMin = lengthGroup.select(`.Min${index}`); // Adjust to match your selector

    // Add a text element showing the value at the current position
    const sliderMaxValueText = lengthGroup
      .append('text')
      .attr('class', `slider-max${index}`)
      .attr('x', 40 + xOffset) // Adjust position
      .attr('y', 10 + 140 * (1 - (currentSliderMaxValue - data.minV) / (data.maxV - data.minV))) // Adjust position
      .style('font-size', '12px') // Adjust font size
      .style('fill', 'black'); // Adjust font color
    // Add a text element showing the value at the current position
    const sliderMinValueText = lengthGroup
      .append('text')
      .attr('class', `slider-min${index}`)
      .attr('x', 40 + xOffset) // Adjust position
      .attr('y', 10 + 140 * (1 - (currentSliderMinValue - data.minV) / (data.maxV - data.minV))) // Adjust position
      .style('font-size', '12px') // Adjust font size
      .style('fill', 'black'); // Adjust font color
    // Update the slider value text

    sliderMaxValueText.text(
      currentSliderMaxValue ? currentSliderMaxValue.toFixed(colorBarDecimal) : data.maxV,
    );
    sliderMinValueText.text(
      currentSliderMinValue ? currentSliderMinValue.toFixed(colorBarDecimal) : data.minV,
    );

    // Define the slider drag behavior
    const dragMax = d3.drag().on('drag', dragMaxHandler).on('end', dragEndMaxHandler);
    const dragMin = d3.drag().on('drag', dragHandlerMin).on('end', dragEndHandlerMin);

    // Apply the drag behavior to the slider handles
    sliderMax.call(dragMax);
    sliderMin.call(dragMin);

    // Drag event handler
    function dragMaxHandler() {
      // Get the slider position
      const newY = Math.min(140, Math.max(0, d3.event.y));

      sliderMax.attr('y', newY);
      sliderMaxValueText.attr('y', newY + 10);

      // Compute the corresponding value from the slider position
      const range = data.maxV - data.minV;
      currentSliderMaxValue = data.minV + (1 - newY / 140) * range;
      // Update the label below the slider handle
      lengthGroup.selectAll('.slider-max').text(currentSliderMaxValue.toFixed(colorBarDecimal));
      // sliderMax.style('fill', colorScale(currentSliderMinValue));
      // Update the slider value text
      sliderMaxValueText.text(currentSliderMaxValue.toFixed(colorBarDecimal));
      if (currentSliderMaxValue > currentSliderMinValue) {
        colorBarRange.current = [currentSliderMinValue, currentSliderMaxValue];
      } else {
        colorBarRange.current = [currentSliderMaxValue, currentSliderMinValue];
      }

      changeCellFilterByObsContinuous(colorBarRange.current, data.name);
    }

    // Drag-end event handler
    function dragEndMaxHandler() {
      // On drag end, clamp the slider value to the range
      currentSliderMaxValue = Math.max(data.minV, Math.min(data.maxV, currentSliderMaxValue));
      // Update the slider position from the new slider value
      const positionPercentage = (currentSliderMaxValue - data.minV) / (data.maxV - data.minV);
      const newY = 140 * (1 - positionPercentage);

      // Update the label below the slider handle
      lengthGroup.selectAll('.slider-max').text(currentSliderMaxValue.toFixed(colorBarDecimal));
      if (currentSliderMaxValue > currentSliderMinValue) {
        colorBarRange.current = [currentSliderMinValue, currentSliderMaxValue];
      } else {
        colorBarRange.current = [currentSliderMaxValue, currentSliderMinValue];
      }
      changeCellFilterByObsContinuous(colorBarRange.current, data.name);
      // Update the slider value text
      sliderMaxValueText.text(currentSliderMaxValue.toFixed(colorBarDecimal));

      // Update the slider position
      sliderMax.attr('y', newY);
      sliderMaxValueText.attr('y', newY + 10);
    }

    // Drag event handler for sliderMin
    function dragHandlerMin() {
      // Get the slider position
      const newY = Math.min(140, Math.max(0, d3.event.y));
      sliderMinValueText.attr('y', newY + 10);
      sliderMin.attr('y', newY);

      // Compute the corresponding value from the slider position
      const range = data.maxV - data.minV;
      currentSliderMinValue = data.minV + (1 - newY / 140) * range;
      // sliderMin.style('fill', colorScale(currentSliderMaxValue));
      sliderMinValueText.text(currentSliderMinValue.toFixed(colorBarDecimal));
      // Update the label below the slider handle
      lengthGroup.selectAll('.sliderMinValue').text(currentSliderMinValue.toFixed(colorBarDecimal));
      if (currentSliderMaxValue > currentSliderMinValue) {
        colorBarRange.current = [currentSliderMinValue, currentSliderMaxValue];
      } else {
        colorBarRange.current = [currentSliderMaxValue, currentSliderMinValue];
      }
      changeCellFilterByObsContinuous(colorBarRange.current, data.name);
    }

    // Drag-end event handler for sliderMin
    function dragEndHandlerMin() {
      // On drag end, clamp the slider value to the range
      currentSliderMinValue = Math.max(data.minV, Math.min(data.maxV, currentSliderMinValue));

      // Update the slider position from the new slider value
      const positionPercentage = (currentSliderMinValue - data.minV) / (data.maxV - data.minV);
      const newY = 140 * (1 - positionPercentage);

      // Update the slider value text
      lengthGroup.selectAll('.sliderMinValue').text(currentSliderMinValue.toFixed(colorBarDecimal));

      // Update the slider position
      sliderMin.attr('y', newY);
      sliderMinValueText.attr('y', newY + 10);
      if (currentSliderMaxValue > currentSliderMinValue) {
        colorBarRange.current = [currentSliderMinValue, currentSliderMaxValue];
      } else {
        colorBarRange.current = [currentSliderMaxValue, currentSliderMinValue];
      }
      changeCellFilterByObsContinuous(colorBarRange.current, data.name);
    }
  };

  const drawLegendByObsContinuous = async () => {
    if (!legendLayerRef.current) {
      return;
    }
    const svg = d3.select(legendLayerRef.current);
    const lengthGroup = svg
      .select('.legend')
      .attr(
        'transform',
        LegendDirection === 'vertical'
          ? `translate(${10}, ${0})`
          : `rotate(90) translate(${10}, ${-150})`,
      );

    lengthGroup.selectAll('*').remove();

    if (legendData && legendData.length > 0) {
      const legendWidth = colorBarWidth; // Height of each individual legend

      // Loop through each item in the legendData array

      legendData.forEach(async (item, index) => {
        const xOffset = index * legendWidth;

        const gradient = lengthGroup
          .append('defs')
          .append('linearGradient')
          .attr('id', `legendGradient_${index}`)
          .attr('x1', '0%')
          .attr('y1', '0%')
          .attr('x2', '0%')
          .attr('y2', '100%');

        gradient
          .append('stop')
          .attr('offset', `0%`)
          .attr('stop-color', item.color)
          .attr('stop-opacity', 1);

        gradient
          .append('stop')
          .attr('offset', `100%`)
          .attr('stop-color', item.color)
          .attr('stop-opacity', 0);

        lengthGroup
          .append('rect')
          .attr('x', xOffset)
          .attr('y', 0)
          .attr('width', 30) // Width
          .attr('height', 145) // Height
          .style('fill', `url(#legendGradient_${index})`);
        // let currentSliderMaxValue = item.maxV; // Current slider value
        // let currentSliderMinValue = item.minV; // Current slider value

        // Add labels
        lengthGroup
          .append('text')
          .attr('x', 40 + xOffset) // Label x position
          .attr('y', 140) // Label y position
          .style('user-select', 'none')
          .style('font-size', fontSize.legend)
          .style('color', fontColor.legend)
          .style('font-family', fontFamily.legend)
          .text(item.minV ? item.minV.toFixed(colorBarDecimal) : item.minV);

        lengthGroup
          .append('text')
          .attr('x', 40 + xOffset)
          .attr('y', 20)
          .style('user-select', 'none')
          .style('font-size', fontSize.legend)
          .style('color', fontColor.legend)
          .style('font-family', fontFamily.legend)
          .text(item.maxV ? item.maxV.toFixed(colorBarDecimal) : item.maxV);
        setupSliderByObsContinuous(item, index, lengthGroup, colorBarDecimal, xOffset);
      });
    }
  };

  useEffect(() => {
    if (colorMode === ColorMode.CATEGORY_OBS) {
      drawLegend();
    } else if (
      colorMode === ColorMode.CONTINUOUS_X_COL_AVG ||
      colorMode === ColorMode.CONTINUOUS_XCOL
    ) {
      if (!legendData) return;
      legendData.name = colorKey;
      drawLegendByContinuous([legendData]);
    } else if (colorMode === ColorMode.CONTINUOUS_X_COL_MULTIPLE) {
      if (!legendData) return;
      drawLegendByContinuous(legendData);
    } else if (
      colorMode === ColorMode.CONTINUOUS_XCOL_MONOCHROME ||
      colorMode === ColorMode.CONTINUOUS_X_COL_AVG_MONOCHROME
    ) {
      drawLegendByObsContinuous();
    } else if (colorMode === ColorMode.CONTINUOUS_OBS_MULTIPLE) {
      if (obsContinuousMode === 'LegendByContinuous') {
        drawLegend();
      } else {
        if (!legendData) return;
        drawLegendByContinuous(legendData);
      }
    }
  }, [
    chartSize,
    scales,
    legendData,
    colorMode,
    chartOptions,
    geneColorMode,
    { ...cellSelectorFilter.continuousColValueRangeMap },
  ]);

  useEffect(() => {
    if (colorMode === ColorMode.CATEGORY_OBS && legendData && legendData.length) {
      const newLegendHeight = Math.ceil(legendData.length / legendCol) * legendHeight;
      setSetSvgSize({
        ...svgSize,
        width: legendWidth * legendCol,
        height: newLegendHeight,
      });
      if (LegendDirection === 'vertical') {
        setSetSvgSize({
          ...svgSize,
          width: legendWidth * legendCol,
          height: newLegendHeight,
        });
      } else if (LegendDirection === 'horizontal') {
        setSetSvgSize({
          ...svgSize,
          width: newLegendHeight,
          height: legendWidth * legendCol,
        });
      }
    } else if (legendData && legendData.length) {
      const newWidth = colorBarWidth * legendData.length;
      if (LegendDirection === 'vertical') {
        setSetSvgSize({
          ...svgSize,
          width: newWidth,
          height: 150,
        });
      } else if (LegendDirection === 'horizontal') {
        setSetSvgSize({
          ...svgSize,
          width: 150,
          height: newWidth,
        });
      }
    } else {
      if (LegendDirection === 'vertical') {
        setSetSvgSize({
          ...svgSize,
          width: 50,
          height: 150,
        });
      } else if (LegendDirection === 'horizontal') {
        setSetSvgSize({
          ...svgSize,
          width: 150,
          height: 50,
        });
      }
    }
  }, [LegendDirection, legendLayout, colorMode, legendWidth, legendCol, legendHeight, legendData]);

  return (
    <div
      style={{
        position: 'absolute',
        left: ((chartSize.width - svgSize.width) * legendLeft) / 100,
        top: ((chartSize.height - svgSize.height) * legendTop) / 100,
        zIndex: 100,
        transformOrigin: 'right bottom',
        height:
          chartSize.height > svgSize.height || chartSize.height == svgSize.height
            ? svgSize.height
            : chartSize.height, // Set the container height
        overflowY: 'auto', // Enable the vertical scrollbar
      }}
    >
      <svg
        ref={legendLayerRef}
        width={svgSize.width}
        style={{
          width: '100%', // Set the SVG width to fill the container
          height: svgSize.height,
        }}
      >
        <g
          className="legend"
          onClick={(e) => {
            e.stopPropagation();
          }}
        />
      </svg>
    </div>
  );
};
