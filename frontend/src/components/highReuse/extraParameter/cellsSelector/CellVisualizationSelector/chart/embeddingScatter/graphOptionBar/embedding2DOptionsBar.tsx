import {
  BgColorsOutlined,
  BorderOuterOutlined,
  EnterOutlined,
  MinusCircleOutlined,
  OneToOneOutlined,
  ProfileOutlined,
  ToolOutlined,
  UngroupOutlined,
} from '@ant-design/icons';
import {
  Button,
  Divider,
  Input,
  InputNumber,
  Popover,
  Radio,
  Select,
  Slider,
  Space,
  Switch,
  Tooltip,
} from 'antd';

import { ExtraIcon } from '@/components/common/extraIcon';
import { useState } from 'react';
import { ChromePicker } from 'react-color';
import { useModel } from 'umi';
import styles from './bar.css';

const Embedding2DOptionsBar = () => {
  const {
    chartOptionDic,
    setChartOptionDic,
    // activeKey,
    // embeddingMode,
    currentOptionsBarExpanded,
    setCurrentOptionsBarExpanded,
  } = useModel('cellSelect');

  const [legendSelected, setLegendSelected] = useState('graphical symbol');
  // const [obsContinuousMode, setObsContinuousMode] = useState<string>('LegendByContinuous');

  const {
    name,
    lineColor,
    componentSize,
    backgroundColor,
    aspectRatio,
    fontSize,
    fontFamily,
    fontColor,
    axisOfDistance,
    xLabelOfDistance,
    yLabelOfDistance,
    axisSize,
    legendShape,
    LegendDirection,
    legendWidth,
    legendHeight,
    legendCol,
    isShowBorder,
    scaleIdentification,
    legendTop,
    legendLeft,
    smallAxisSize,
    colorBarWidth,
    colorBarDecimal,
    backgroundAlpha,
    // obsContinuousMode,
  } = chartOptionDic.EmbeddingD3ChartOptions;

  const toggleGraphOptionBar = () => {
    setCurrentOptionsBarExpanded(!currentOptionsBarExpanded);
  };

  const onChange = (value: number | null) => {
    if (value) {
      setChartOptionDic({
        ...chartOptionDic,
        EmbeddingD3ChartOptions: {
          ...chartOptionDic.EmbeddingD3ChartOptions,
          componentSize: value,
        },
      });
    }
  };

  const typeFace = [
    {
      value: 'Roboto',
      label: 'Roboto',
    },
    {
      value: 'Open Sans',
      label: 'Open Sans',
    },
    {
      value: 'Lato',
      label: 'Lato',
    },
    {
      value: 'Ubuntu',
      label: 'Ubuntu',
    },
    {
      value: 'Source Sans Pro',
      label: 'Source Sans Pro',
    },
    {
      value: 'Fira Sans',
      label: 'Fira Sans',
    },
    {
      value: 'Noto Sans',
      label: 'Noto Sans',
    },
    {
      value: 'Cabin',
      label: 'Cabin',
    },
    {
      value: 'Quicksand',
      label: 'Quicksand',
    },
    {
      value: 'Playfair Display',
      label: 'Playfair Display',
    },
  ];

  return currentOptionsBarExpanded ? (
    <div
      className={styles.bar}
      style={{
        position: 'absolute',
        width: 40,
        height: '100%',
        top: 0,
        right: 0,
        backgroundColor: 'white',
        zIndex: 999,
      }}
    >
      <div
        className={styles.buttonGroup}
        style={{
          flex: 12,
        }}
      >
        <Tooltip placement="left" title="fold the options bar">
          <MinusCircleOutlined className={styles.button} onClick={toggleGraphOptionBar} />
        </Tooltip>
        {/* Aspect ratio */}
        <Popover
          placement="left"
          trigger="click"
          content={
            <Space direction="horizontal" align="center">
              aspect ratio:
              <div>1</div>:
              <InputNumber
                min={0.56}
                step={0.01}
                max={1}
                defaultValue={aspectRatio}
                style={{ width: '120px', marginLeft: '0.5vw' }}
                onChange={(value: any) => {
                  setChartOptionDic({
                    ...chartOptionDic,
                    EmbeddingD3ChartOptions: {
                      ...chartOptionDic.EmbeddingD3ChartOptions,
                      aspectRatio: value,
                    },
                  });
                }}
              />
            </Space>
          }
        >
          <OneToOneOutlined className={styles.button} />
        </Popover>
        {/* axis */}
        <Popover
          placement="leftTop"
          trigger="click"
          title={<div style={{ fontWeight: 'bold', fontSize: '18' }}>Coordinate axis edit</div>}
          content={
            <Space direction="vertical" align="end">
              {/* Full axes / compact axes */}
              <Space>
                coordinate type:
                <Radio.Group
                  defaultValue={axisSize}
                  style={{ width: 120, marginLeft: '0.5vw' }}
                  buttonStyle="solid"
                  size="small"
                  onChange={(e) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        axisSize: e.target.value,
                      },
                    });
                  }}
                >
                  <Radio.Button value={'default'}>default</Radio.Button>
                  <Radio.Button value={'small'}>small</Radio.Button>
                </Radio.Group>
              </Space>
              {/* Length of the compact axes */}
              <Space>
                axis length:
                <InputNumber
                  min={0.1}
                  max={1}
                  step={0.1}
                  defaultValue={smallAxisSize}
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        smallAxisSize: value,
                      },
                    });
                  }}
                />
              </Space>
              {/* Edge width */}
              <Space direction="horizontal">
                line width:
                <InputNumber
                  min={1}
                  defaultValue={1}
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        lineWeight: value,
                      },
                    });
                  }}
                />
              </Space>
              {/* Edge color */}
              <Space>
                line color:
                <Popover
                  placement="right"
                  trigger="click"
                  content={
                    <ChromePicker
                      disableAlpha
                      color={lineColor}
                      onChange={(color: any) => {
                        setChartOptionDic({
                          ...chartOptionDic,
                          EmbeddingD3ChartOptions: {
                            ...chartOptionDic.EmbeddingD3ChartOptions,
                            lineColor: color.hex,
                          },
                        });
                      }}
                    />
                  }
                >
                  <div style={{ width: '120px', marginLeft: '0.5vw' }}>
                    <div
                      style={{
                        height: 20,
                        borderRadius: 5,
                        marginLeft: '0.5vw',
                        width: '20px',
                        cursor: 'pointer',
                        backgroundColor: lineColor,
                        border: '1px solid rgba(0,0,0,0.3)',
                      }}
                    />
                  </div>
                </Popover>
              </Space>
              {/* X-axis name */}
              <Space>
                x label name:
                <Input
                  placeholder={name.x}
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
                    e.stopPropagation();
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        name: { x: e.target.value, y: name.y },
                      },
                    });
                  }}
                />
              </Space>
              {/* Y-axis name */}
              <Space>
                y label name:
                <Input
                  placeholder={name.y}
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
                    e.stopPropagation();
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        name: {
                          x: name.x,
                          y: e.target.value,
                        },
                      },
                    });
                  }}
                />
              </Space>
              {/* Axis label font size */}
              <Space>
                x/y label font size:
                <InputNumber
                  min={12}
                  defaultValue={fontSize.xy}
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        fontSize: { xy: value, label: fontSize.label, legend: fontSize.legend },
                      },
                    });
                  }}
                />
              </Space>
              {/* Axis label font family */}
              <Space>
                x/y label font:
                <Select
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  options={typeFace}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        fontFamily: {
                          xy: value,
                          compontentLabel: fontFamily.compontentLabel,
                          legend: fontFamily.legend,
                        },
                      },
                    });
                  }}
                />
              </Space>
              {/* Axis label font color */}
              <Space style={{ display: 'flex' }}>
                x/y label color:
                <Popover
                  placement="right"
                  trigger="click"
                  content={
                    <ChromePicker
                      disableAlpha
                      color={fontColor.xy}
                      onChange={(color: any) => {
                        setChartOptionDic({
                          ...chartOptionDic,
                          EmbeddingD3ChartOptions: {
                            ...chartOptionDic.EmbeddingD3ChartOptions,
                            fontColor: {
                              xy: color.hex,
                              compontentLabel: fontColor.compontentLabel,
                              legend: fontColor.legend,
                            },
                          },
                        });
                      }}
                    />
                  }
                >
                  <div style={{ width: '120px', marginLeft: '0.5vw' }}>
                    <div
                      style={{
                        height: 20,
                        borderRadius: 5,
                        marginLeft: '0.5vw',
                        width: '20px',
                        cursor: 'pointer',
                        backgroundColor: fontColor.xy,
                        border: '1px solid rgba(0,0,0,0.3)',
                      }}
                    />
                  </div>
                </Popover>
              </Space>
              {/* Distance between the x-axis label and the axis */}
              <Space>
                coordinate axis - x label:
                <InputNumber
                  defaultValue={xLabelOfDistance}
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        xLabelOfDistance: value,
                      },
                    });
                  }}
                />
              </Space>
              {/* Distance between the y-axis label and the axis */}
              <Space>
                coordinate axis - y label:
                <InputNumber
                  defaultValue={yLabelOfDistance}
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        yLabelOfDistance: value,
                      },
                    });
                  }}
                />
              </Space>
              {/* Distance between ticks and tick labels */}
              <Space>
                coordinate axis - scale:
                <InputNumber
                  // min={0}
                  // max={10}
                  defaultValue={axisOfDistance}
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        axisOfDistance: value,
                      },
                    });
                  }}
                />
              </Space>
              {/* Show/hide tick labels */}
              <Space>
                x/y ticks:
                <div style={{ width: '120px', marginLeft: '0.5vw' }}>
                  <Switch
                    // style={{ marginLeft: '0.5vw' }}
                    checked={scaleIdentification}
                    onChange={(checked: any) => {
                      setChartOptionDic({
                        ...chartOptionDic,
                        EmbeddingD3ChartOptions: {
                          ...chartOptionDic.EmbeddingD3ChartOptions,
                          scaleIdentification: checked,
                        },
                      });
                    }}
                  />
                </div>
              </Space>
            </Space>
          }
        >
          <Button
            size="small"
            type="text"
            icon={<EnterOutlined rotate={90} type="icon-touming" />}
          />
        </Popover>
        {/* label */}
        <Popover
          placement="leftTop"
          trigger="click"
          title={<div style={{ fontWeight: 'bold', fontSize: '18' }}>Component label edit</div>}
          content={
            <Space direction="vertical" align="end">
              {/* Label size */}
              <Space direction="horizontal">
                component label:
                <InputNumber
                  min={12}
                  defaultValue={16}
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        fontSize: { xy: fontSize.xy, label: value, legend: fontSize.legend },
                      },
                    });
                  }}
                />
              </Space>
              {/* Label font family */}
              <Space>
                component label font:
                <Select
                  style={{ width: '120px', marginLeft: '0.5vw' }}
                  options={typeFace}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        fontFamily: {
                          xy: fontFamily.xy,
                          compontentLabel: value,
                          legend: fontFamily.legend,
                        },
                      },
                    });
                  }}
                />
              </Space>
              {/* Label color */}
              <Space>
                component label color:
                <Popover
                  placement="right"
                  trigger="click"
                  content={
                    <ChromePicker
                      disableAlpha
                      color={fontColor.compontentLabel}
                      onChange={(color: any) => {
                        setChartOptionDic({
                          ...chartOptionDic,
                          EmbeddingD3ChartOptions: {
                            ...chartOptionDic.EmbeddingD3ChartOptions,
                            fontColor: {
                              xy: fontColor.xy,
                              compontentLabel: color.hex,
                              legend: fontColor.legend,
                            },
                          },
                        });
                      }}
                    />
                  }
                >
                  <div style={{ width: '120px', marginLeft: '0.5vw' }}>
                    <div
                      style={{
                        height: 20,
                        borderRadius: 5,
                        marginLeft: '0.5vw',
                        width: '20px',
                        cursor: 'pointer',
                        backgroundColor: fontColor.compontentLabel,
                        border: '1px solid rgba(0,0,0,0.3)',
                      }}
                    />
                  </div>
                </Popover>
              </Space>
            </Space>
          }
        >
          <Button size="small" type="text" icon={<ExtraIcon type="icon-text" />} />
        </Popover>
        {/* legend */}
        <Popover
          placement="leftTop"
          trigger="click"
          title={<div style={{ fontWeight: 'bold', fontSize: '18' }}>legend edit</div>}
          content={
            <Space direction="vertical" align="end">
              {/* Legend form selection */}
              <Space direction="horizontal">
                legend style:
                <Radio.Group
                  defaultValue={legendSelected}
                  style={{ width: 200, marginLeft: '0.5vw' }}
                  buttonStyle="solid"
                  size="small"
                  onChange={(e) => {
                    setLegendSelected(e.target.value);
                  }}
                >
                  <Radio.Button value={'graphical symbol'}>graphical symbol</Radio.Button>
                  <Radio.Button value={'color bar'}>color bar</Radio.Button>
                </Radio.Group>
              </Space>
              {/* Move top */}
              <Space align="start">
                <div style={{ marginTop: '0.2vw' }}>position:</div>
                <Space direction="vertical" style={{ width: '200px', marginLeft: '0.5vw' }}>
                  <Space>
                    x:
                    <Slider
                      defaultValue={legendLeft}
                      style={{ width: '160px', marginLeft: '0.5vw' }}
                      onChange={(value: any) => {
                        setChartOptionDic({
                          ...chartOptionDic,
                          EmbeddingD3ChartOptions: {
                            ...chartOptionDic.EmbeddingD3ChartOptions,
                            legendLeft: value,
                          },
                        });
                      }}
                    />
                  </Space>
                  <Space>
                    y:
                    <Slider
                      defaultValue={legendTop}
                      style={{ width: '160px', marginLeft: '0.5vw' }}
                      onChange={(value: any) => {
                        setChartOptionDic({
                          ...chartOptionDic,
                          EmbeddingD3ChartOptions: {
                            ...chartOptionDic.EmbeddingD3ChartOptions,
                            legendTop: value,
                          },
                        });
                      }}
                    />
                  </Space>
                </Space>
                {/* Move left */}
              </Space>
              {/* Font size */}
              <Space>
                legend label font size:
                <InputNumber
                  min={12}
                  defaultValue={16}
                  style={{ width: '200px', marginLeft: '0.5vw' }}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        fontSize: { xy: fontSize.xy, label: fontSize.label, legend: value },
                      },
                    });
                  }}
                />
              </Space>
              {/* <Space>
                legend change:
                <Radio.Group
                  defaultValue={obsContinuousMode}
                  style={{ width: 200, marginLeft: '0.5vw' }}
                  buttonStyle="solid"
                  size="small"
                  onChange={(e) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        obsContinuousMode: e.target.value,
                      },
                    });
                  }}
                >
                  <Radio.Button value={'LegendByContinuous'}>LegendByContinuous</Radio.Button>
                  <Radio.Button value={'color bar'}>color bar</Radio.Button>
                </Radio.Group>
              </Space> */}
              {/* Font family */}
              <Space>
                legend label font:
                <Select
                  style={{ width: '200px', marginLeft: '0.5vw' }}
                  options={typeFace}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        fontFamily: {
                          xy: fontFamily.xy,
                          compontentLabel: fontFamily.compontentLabel,
                          legend: value,
                        },
                      },
                    });
                  }}
                />
              </Space>
              {/* Font color */}
              <Space>
                legend label color:
                <Popover
                  placement="right"
                  trigger="click"
                  content={
                    <ChromePicker
                      disableAlpha
                      color={fontColor.legend}
                      onChange={(color: any) => {
                        setChartOptionDic({
                          ...chartOptionDic,
                          EmbeddingD3ChartOptions: {
                            ...chartOptionDic.EmbeddingD3ChartOptions,
                            fontColor: {
                              xy: fontColor.xy,
                              compontentLabel: fontColor.compontentLabel,
                              legend: color.hex,
                            },
                          },
                        });
                      }}
                    />
                  }
                >
                  <div style={{ width: '200px', marginLeft: '0.5vw' }}>
                    <div
                      style={{
                        height: 20,
                        borderRadius: 5,
                        marginLeft: '0.5vw',
                        width: '20px',
                        cursor: 'pointer',
                        backgroundColor: fontColor.legend,
                        border: '1px solid rgba(0,0,0,0.3)',
                      }}
                    />
                  </div>
                </Popover>
              </Space>
              {/* Color swatch shape */}
              {legendSelected === 'graphical symbol' && (
                <Space>
                  element shape:
                  <Radio.Group
                    defaultValue={legendShape}
                    style={{ width: 200, marginLeft: '0.5vw' }}
                    buttonStyle="solid"
                    size="small"
                    onChange={(e) => {
                      setChartOptionDic({
                        ...chartOptionDic,
                        EmbeddingD3ChartOptions: {
                          ...chartOptionDic.EmbeddingD3ChartOptions,
                          legendShape: e.target.value,
                        },
                      });
                    }}
                  >
                    <Radio.Button value={'square'}>square</Radio.Button>
                    <Radio.Button value={'round'}>round</Radio.Button>
                  </Radio.Group>
                </Space>
              )}
              {/* Legend orientation */}
              <Space>
                alignment:
                <Radio.Group
                  defaultValue={LegendDirection}
                  style={{ width: 200, marginLeft: '0.5vw' }}
                  buttonStyle="solid"
                  size="small"
                  onChange={(e) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        LegendDirection: e.target.value,
                      },
                    });
                  }}
                >
                  <Radio.Button value={'vertical'}>vertical</Radio.Button>
                  <Radio.Button value={'horizontal'}>horizontal</Radio.Button>
                </Radio.Group>
              </Space>
              {/* Number of rows/columns */}
              {legendSelected === 'graphical symbol' && (
                <Space>
                  columns:
                  <InputNumber
                    min={1}
                    defaultValue={legendCol}
                    style={{ width: '200px', marginLeft: '0.5vw' }}
                    onChange={(value: any) => {
                      setChartOptionDic({
                        ...chartOptionDic,
                        EmbeddingD3ChartOptions: {
                          ...chartOptionDic.EmbeddingD3ChartOptions,
                          legendCol: value,
                        },
                      });
                    }}
                  />
                </Space>
              )}
              {/* Width */}
              {legendSelected === 'graphical symbol' && (
                <Space>
                  width:
                  <InputNumber
                    defaultValue={legendWidth}
                    style={{ width: '200px', marginLeft: '0.5vw' }}
                    onChange={(value: any) => {
                      setChartOptionDic({
                        ...chartOptionDic,
                        EmbeddingD3ChartOptions: {
                          ...chartOptionDic.EmbeddingD3ChartOptions,
                          legendWidth: value,
                        },
                      });
                    }}
                  />
                </Space>
              )}
              {/* Height */}
              {legendSelected === 'graphical symbol' && (
                <Space>
                  height:
                  <InputNumber
                    min={25}
                    defaultValue={legendHeight}
                    style={{ width: '200px', marginLeft: '0.5vw' }}
                    onChange={(value: any) => {
                      setChartOptionDic({
                        ...chartOptionDic,
                        EmbeddingD3ChartOptions: {
                          ...chartOptionDic.EmbeddingD3ChartOptions,
                          legendHeight: value,
                        },
                      });
                    }}
                  />
                </Space>
              )}
              {/* color bar height */}
              {legendSelected === 'color bar' && (
                <Space>
                  width:
                  <InputNumber
                    min={25}
                    defaultValue={colorBarWidth}
                    style={{ width: '200px', marginLeft: '0.5vw' }}
                    onChange={(value: any) => {
                      setChartOptionDic({
                        ...chartOptionDic,
                        EmbeddingD3ChartOptions: {
                          ...chartOptionDic.EmbeddingD3ChartOptions,
                          colorBarWidth: value,
                        },
                      });
                    }}
                  />
                </Space>
              )}
              {/* color bar decimal places */}
              {legendSelected === 'color bar' && (
                <Space>
                  accuracy:
                  <InputNumber
                    min={0}
                    max={10}
                    defaultValue={colorBarDecimal}
                    style={{ width: '200px', marginLeft: '0.5vw' }}
                    onChange={(value: any) => {
                      setChartOptionDic({
                        ...chartOptionDic,
                        EmbeddingD3ChartOptions: {
                          ...chartOptionDic.EmbeddingD3ChartOptions,
                          colorBarDecimal: value,
                        },
                      });
                    }}
                  />
                </Space>
              )}
              {/* Category background opacity */}
              <Space>
                background alpha:
                <Slider
                  defaultValue={backgroundAlpha}
                  min={0}
                  max={1}
                  step={0.1}
                  style={{ width: '160px', marginLeft: '0.5vw' }}
                  onChange={(value: any) => {
                    setChartOptionDic({
                      ...chartOptionDic,
                      EmbeddingD3ChartOptions: {
                        ...chartOptionDic.EmbeddingD3ChartOptions,
                        backgroundAlpha: value,
                      },
                    });
                  }}
                />
              </Space>
            </Space>
          }
        >
          <Button size="small" type="text" icon={<ProfileOutlined type="icon-touming" />} />
        </Popover>
      </div>
      <Divider />
      <div
        className={styles.buttonGroup}
        style={{
          flex: 6,
        }}
      >
        {/* Point size */}
        <Popover
          placement="left"
          trigger="click"
          content={
            <Space direction="horizontal" align="center">
              component size:
              <InputNumber
                min={1}
                defaultValue={componentSize}
                style={{ width: '120px', marginLeft: '0.5vw' }}
                onChange={onChange}
              />
            </Space>
          }
        >
          <Button size="small" type="text" icon={<UngroupOutlined />} />
        </Popover>
        {/* Background color */}
        <Popover
          placement="left"
          trigger="click"
          content={
            <Space direction="vertical" align="end">
              <div style={{ display: 'flex' }}>
                background color:
                <Popover
                  placement="right"
                  trigger="click"
                  content={
                    <ChromePicker
                      disableAlpha
                      color={backgroundColor}
                      onChange={(color: any) => {
                        setChartOptionDic({
                          ...chartOptionDic,
                          EmbeddingD3ChartOptions: {
                            ...chartOptionDic.EmbeddingD3ChartOptions,
                            backgroundColor: color.hex,
                          },
                        });
                      }}
                    />
                  }
                >
                  <div
                    style={{
                      height: 20,
                      borderRadius: 5,
                      width: '20px',
                      marginLeft: '0.5vw',
                      cursor: 'pointer',
                      backgroundColor: backgroundColor,
                      border: '1px solid rgba(0,0,0,0.3)',
                    }}
                  />
                </Popover>
              </div>
            </Space>
          }
        >
          <BgColorsOutlined className={styles.button} />
        </Popover>
      </div>
      <Divider />
      <div
        className={styles.buttonGroup}
        style={{
          flex: 3,
        }}
      >
        {/* Border */}
        <Popover
          placement="left"
          trigger="click"
          content={
            <Space direction="horizontal" align="center">
              image border:
              <Switch
                style={{ marginLeft: '0.5vw' }}
                checked={isShowBorder}
                onChange={(checked: any) => {
                  setChartOptionDic({
                    ...chartOptionDic,
                    EmbeddingD3ChartOptions: {
                      ...chartOptionDic.EmbeddingD3ChartOptions,
                      isShowBorder: checked,
                    },
                  });
                }}
              />
            </Space>
          }
        >
          <BorderOuterOutlined className={styles.button} />
        </Popover>
      </div>
    </div>
  ) : (
    <div
      className={styles.floatOpenButton}
      // onKeyPress={noop}
    >
      <Button onClick={toggleGraphOptionBar} icon={<ToolOutlined style={{ color: '#888' }} />} />
    </div>
  );
};

export default Embedding2DOptionsBar;
