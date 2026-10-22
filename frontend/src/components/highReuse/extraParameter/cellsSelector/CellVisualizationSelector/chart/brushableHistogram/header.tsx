// Adapted from cellxgene (https://github.com/chanzuckerberg/cellxgene),
// Copyright (c) Chan Zuckerberg Initiative. MIT License; see THIRD_PARTY_NOTICES.md.
import React, { useCallback } from 'react';
import { Button, Tooltip, Row, Col } from 'antd';
import { DotChartOutlined } from '@ant-design/icons';
import { ExtraIcon } from '@/components/common/extraIcon';

const HistogramHeader = React.memo(
  ({
    fieldId,
    isColorBy,
    onColorByClick,
    onRemoveClick,
    isScatterPlotX,
    isScatterPlotY,
    onScatterPlotXClick,
    onScatterPlotYClick,
    isObs,
  }: any) => {
    /*
        Render the toolbar for the histogram.  Props:
          * fieldId - field identifier, used for various IDs
          * isColorBy - true/false, is this the current color-by
          * onColorByClick - color-by click handler
          * onRemoveClick - optional handler for remove.  Button will not render if not defined.
          * isScatterPlotX - optional, true/false if currently the X scatterplot field
          * isScatterPlotY - optional, true/false if currently the Y scatterplot field
          * onScatterPlotXClick - optional, handler for scatterPlot X button.
          * onScatterPlotYClick - optional, handler for scatterPlot X button.
  
        Scatterplot controls will not render if either handler unspecified.
      */

    const memoizedColorByCallback = useCallback(
      () => onColorByClick(fieldId, isObs),
      [fieldId, isObs],
    );

    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          paddingBottom: '8px',
        }}
      >
        {onScatterPlotXClick && onScatterPlotYClick ? (
          <span>
            <DotChartOutlined />
            <Row>
              <Col span={12}>
                <Button onClick={onScatterPlotXClick} type={isScatterPlotX ? 'primary' : 'default'}>
                  plot x
                </Button>
              </Col>
              <Col span={12}>
                <Button onClick={onScatterPlotYClick} type={isScatterPlotY ? 'primary' : 'default'}>
                  plot y
                </Button>
              </Col>
            </Row>
          </span>
        ) : null}
        {onRemoveClick ? (
          <Button size="small" onClick={onRemoveClick} type="default">
            remove
          </Button>
        ) : null}
        <Tooltip content="Use as color scale" position="bottom">
          <Button
            onClick={memoizedColorByCallback}
            icon={<ExtraIcon type="icon-drop" />}
            type={isColorBy ? 'primary' : 'default'}
          />
        </Tooltip>
      </div>
    );
  },
);

export default HistogramHeader;
