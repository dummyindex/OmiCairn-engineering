import BrushableHistogram from '../chart/brushableHistogram';
import { ColorMode, DimensionSourceType } from '@/constants/cellSelector';
import { writeToClipboard } from '@/util/operationTools';
import { cutString } from '@/util/stringHelpers';
import {
  BgColorsOutlined,
  CopyOutlined,
  DownOutlined,
  EllipsisOutlined,
  ExpandAltOutlined,
  FormatPainterOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { Button, Col, Collapse, Dropdown, Menu, message, Popover, Row } from 'antd';
import chroma from 'chroma-js';
import * as d3 from 'd3';
import { useEffect, useState } from 'react';
import ChromePicker from 'react-color';
import { useModel } from 'umi';

const ColorBand = (props: any) => {
  const { AlternativeColorBand } = props;
  const colorScaleFunction = d3
    .scaleLinear()
    .domain([0, 0.5, 1]) // Define the positions of the three colors here
    .range(AlternativeColorBand);
  const { changeInterpolator, setGeneColorList } = useModel('cellSelect');
  // const colorScale = d3.scaleSequential(colorScaleFunction).domain([1, 0]);

  // const getColorArr = () => {
  //   const colorArr = [];
  //   for (let i = 0.01; i < 1; i += 0.01) {
  //     colorArr.push(colorScale(i));
  //   }
  //   return colorArr;
  // };
  // const colorArr = getColorArr();

  return (
    <div
      style={{
        height: 15,
        width: '60px',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'flex-start',
        alignItems: 'stretch',
        marginTop: '5px',
        marginBottom: '5px',
        // background: `linear-gradient(to right, ${colorScale(1.5)}, ${colorScale(0)})`,
      }}
      onClick={(e) => {
        e.stopPropagation();
        setGeneColorList(AlternativeColorBand);
        changeInterpolator(colorScaleFunction);
      }}
    >
      {AlternativeColorBand.map((bandItem) => {
        return (
          <div
            key={bandItem}
            style={{
              height: '100%',
              width: `25%`,
              // marginRight: '3%',
              backgroundColor: bandItem,
            }}
          />
        );
      })}
    </div>
  );
};

interface GeneProps {
  geneName: string;
  genesetName: string;
  colorArray: any[];
  color: any;
}

const Gene = (props: GeneProps) => {
  const { geneName, genesetName, colorArray, color } = props;

  const {
    colorMode,
    updateColorMode,
    colorKey,
    xColMonochrome,
    setXColMonochrome,
    geneColorList,
    setGeneColorList,
    changeInterpolator,
    xyzDimensions,
    setXyzDimensions,
    dimensionsLoading,
  } = useModel('cellSelect');
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState<boolean>(false);
  const colorActive =
    (colorMode === ColorMode.CONTINUOUS_XCOL && colorKey === geneName) ||
    (colorMode === ColorMode.CONTINUOUS_XCOL_MONOCHROME && colorKey === geneName);
  const [selectedColor, setSelectedColor] = useState('');

  const changeColor = (value: any) => {
    setXColMonochrome({
      [geneName]: [value.rgb.r, value.rgb.g, value.rgb.b, value.rgb.a],
    });
  };

  const xActive = xyzDimensions[0]
    ? xyzDimensions[0].dimSource === DimensionSourceType.X_COL && xyzDimensions[0].dim === geneName
    : false;
  const yActive = xyzDimensions[1]
    ? xyzDimensions[1].dimSource === DimensionSourceType.X_COL && xyzDimensions[1].dim === geneName
    : false;
  const zActive = xyzDimensions[2]
    ? xyzDimensions[2].dimSource === DimensionSourceType.X_COL && xyzDimensions[2].dim === geneName
    : false;

  return (
    <>
      <Row gutter={5} align="middle" justify="center" style={{ width: '99%' }}>
        <Col>
          <span
            style={{
              fontSize: '0.8em',
            }}
          >
            {geneName}
          </span>
        </Col>
        <Col flex={1} />
        <Col>
          <Button
            size="small"
            type={xActive ? 'primary' : 'text'}
            style={{
              fontSize: '1em',
              fontWeight: 'bold',
            }}
            icon="x"
            loading={dimensionsLoading}
            onClick={() => {
              if (xActive) {
                setXyzDimensions([null, xyzDimensions[1], xyzDimensions[2]]);
              } else {
                setXyzDimensions([
                  {
                    dimSource: DimensionSourceType.X_COL,
                    dim: geneName,
                  },
                  xyzDimensions[1],
                  xyzDimensions[2],
                ]);
              }
            }}
          />
        </Col>
        <Col>
          <Button
            size="small"
            type={yActive ? 'primary' : 'text'}
            style={{
              fontSize: '1em',
              fontWeight: 'bold',
            }}
            loading={dimensionsLoading}
            icon="y"
            onClick={() => {
              if (yActive) {
                setXyzDimensions([xyzDimensions[0], null, xyzDimensions[2]]);
              } else {
                setXyzDimensions([
                  xyzDimensions[0],
                  {
                    dimSource: DimensionSourceType.X_COL,
                    dim: geneName,
                  },
                  xyzDimensions[2],
                ]);
              }
            }}
          />
        </Col>
        <Col>
          <Button
            size="small"
            type={zActive ? 'primary' : 'text'}
            style={{
              fontSize: '1em',
              fontWeight: 'bold',
            }}
            loading={dimensionsLoading}
            icon="z"
            onClick={() => {
              if (zActive) {
                setXyzDimensions([xyzDimensions[0], xyzDimensions[1], null]);
              } else {
                setXyzDimensions([
                  xyzDimensions[0],
                  xyzDimensions[1],
                  {
                    dimSource: DimensionSourceType.X_COL,
                    dim: geneName,
                  },
                ]);
              }
            }}
          />
        </Col>
        <Col>
          <Popover
            content={
              <Row gutter={5}>
                <Col
                  style={{
                    width: '100px',
                  }}
                >
                  <BrushableHistogram
                    field={geneName}
                    isColorAndMarkerAccessor={
                      colorMode === ColorMode.CONTINUOUS_XCOL && colorKey === geneName
                    }
                    isGeneSetSummary={false}
                    isTopGeneSetSummary={false}
                    zebra={false}
                    isObs={false}
                    mini={true}
                    hideAnno={false}
                    loading={loading}
                    setLoading={setLoading}
                  />
                </Col>
                <Col
                  style={{
                    visibility: colorActive ? 'visible' : 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  {selectedColor === 'brush' && (
                    <Popover
                      placement="bottomLeft"
                      content={
                        <div
                          style={{ width: '70px', height: '100px', overflow: 'auto' }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          {colorArray.map((item: any) => {
                            return <ColorBand AlternativeColorBand={item} key={item} />;
                          })}
                        </div>
                      }
                      trigger="click"
                    >
                      <Button
                        size="small"
                        type="text"
                        onClick={(e: any) => {
                          e.stopPropagation();
                        }}
                        icon={<FormatPainterOutlined />}
                        style={{
                          fontSize: '1em',
                          marginRight: '0.1vw',
                        }}
                      />
                    </Popover>
                  )}
                  {selectedColor === 'brush' && (
                    <Popover
                      placement="right"
                      trigger="click"
                      content={
                        <ChromePicker
                          disableAlpha
                          color={geneColorList[0]}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(color: any) => {
                            geneColorList[0] = `rgba(${color.rgb.r},${color.rgb.g}, ${color.rgb.b}, ${color.rgb.a})`;
                            setGeneColorList([...geneColorList]);
                            const colorScaleFunction = d3
                              .scaleLinear()
                              .domain([0, 0.5, 1]) // Define the positions of the three colors here
                              .range(geneColorList);
                            changeInterpolator(colorScaleFunction);
                          }}
                        />
                      }
                    >
                      <Button
                        size="small"
                        type="text"
                        onClick={(e: any) => {
                          e.stopPropagation();
                        }}
                        style={{
                          height: 10,
                          fontSize: '1em',
                          marginRight: '0.1vw',
                          backgroundColor: geneColorList[0],
                        }}
                      />
                    </Popover>
                  )}
                  {selectedColor === 'brush' && (
                    <Popover
                      placement="right"
                      trigger="click"
                      content={
                        <ChromePicker
                          disableAlpha
                          color={geneColorList[1]}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(color: any) => {
                            geneColorList[1] = `rgba(${color.rgb.r},${color.rgb.g}, ${color.rgb.b}, ${color.rgb.a})`;
                            setGeneColorList([...geneColorList]);
                            const colorScaleFunction = d3
                              .scaleLinear()
                              .domain([0, 0.5, 1]) // Define the positions of the three colors here
                              .range(geneColorList);
                            changeInterpolator(colorScaleFunction);
                          }}
                        />
                      }
                    >
                      <Button
                        size="small"
                        type="text"
                        onClick={(e: any) => {
                          e.stopPropagation();
                        }}
                        style={{
                          height: 10,
                          fontSize: '1em',
                          marginRight: '0.1vw',
                          backgroundColor: geneColorList[1],
                        }}
                      />
                    </Popover>
                  )}
                  {selectedColor === 'brush' && (
                    <Popover
                      placement="right"
                      trigger="click"
                      content={
                        <ChromePicker
                          disableAlpha
                          color={geneColorList[2]}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(color: any) => {
                            geneColorList[2] = `rgba(${color.rgb.r},${color.rgb.g}, ${color.rgb.b}, ${color.rgb.a})`;
                            setGeneColorList([...geneColorList]);
                            const colorScaleFunction = d3
                              .scaleLinear()
                              .domain([0, 0.5, 1]) // Define the positions of the three colors here
                              .range(geneColorList);
                            changeInterpolator(colorScaleFunction);
                          }}
                        />
                      }
                    >
                      <Button
                        size="small"
                        type="text"
                        onClick={(e: any) => {
                          e.stopPropagation();
                        }}
                        style={{
                          height: 10,
                          fontSize: '1em',
                          marginRight: '0.1vw',
                          backgroundColor: geneColorList[2],
                        }}
                      />
                    </Popover>
                  )}
                  {selectedColor === '' ||
                    (selectedColor === 'color' && (
                      <Button
                        size="small"
                        type="text"
                        onClick={(e: any) => {
                          e.stopPropagation();
                        }}
                        icon={<FormatPainterOutlined />}
                        style={{
                          fontSize: '1em',
                          visibility: 'hidden',
                          marginRight: '0.1vw',
                        }}
                      />
                    ))}
                  {selectedColor === '' ||
                    (selectedColor === 'color' && (
                      <Button
                        size="small"
                        type="text"
                        onClick={(e: any) => {
                          e.stopPropagation();
                        }}
                        icon={<FormatPainterOutlined />}
                        style={{
                          fontSize: '1em',
                          visibility: 'hidden',
                          marginRight: '0.1vw',
                        }}
                      />
                    ))}
                  {selectedColor === 'color' && (
                    <Popover
                      placement="right"
                      trigger="click"
                      content={
                        <ChromePicker
                          disableAlpha
                          color={color}
                          onClick={(e: any) => {
                            e.stopPropagation();
                          }}
                          onChange={(color: any) => changeColor(color, genesetName)}
                        />
                      }
                    >
                      <Button
                        size="small"
                        style={{
                          // borderRadius: '50%',
                          cursor: 'pointer',
                          backgroundColor: color,
                          height: 10,
                          marginRight: '0.1vw',
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                        }}
                        icon={<FormatPainterOutlined style={{ visibility: 'hidden' }} />}
                      />
                    </Popover>
                  )}
                  {selectedColor === '' && (
                    <Button
                      size="small"
                      type="text"
                      onClick={(e: any) => {
                        e.stopPropagation();
                      }}
                      icon={<FormatPainterOutlined />}
                      style={{
                        fontSize: '1em',
                        visibility: 'hidden',
                        marginRight: '0.1vw',
                      }}
                    />
                  )}
                  {selectedColor === '' && (
                    <Button
                      size="small"
                      type="text"
                      onClick={(e: any) => {
                        e.stopPropagation();
                      }}
                      icon={<FormatPainterOutlined />}
                      style={{
                        fontSize: '1em',
                        visibility: 'hidden',
                        marginRight: '0.1vw',
                      }}
                    />
                  )}
                  {selectedColor === '' && (
                    <Button
                      size="small"
                      type="text"
                      onClick={(e: any) => {
                        e.stopPropagation();
                      }}
                      icon={<FormatPainterOutlined />}
                      style={{
                        fontSize: '1em',
                        visibility: 'hidden',
                        marginRight: '0.1vw',
                      }}
                    />
                  )}
                </Col>
                <Col>
                  <Dropdown
                    overlay={
                      <Menu
                        onClick={(e: any) => {
                          const { domEvent, key } = e;
                          domEvent.stopPropagation();
                          if (key === '1') {
                            // openSaveModal();
                            if (colorActive) {
                              updateColorMode(ColorMode.NO_COLOR, null);
                              setSelectedColor('');
                            } else {
                              updateColorMode(ColorMode.CONTINUOUS_XCOL, geneName);
                              setSelectedColor('brush');
                            }
                          } else if (key === '2') {
                            // openSaveAutoModal();
                            if (colorActive) {
                              updateColorMode(ColorMode.NO_COLOR, null);
                              setSelectedColor('');
                            } else {
                              updateColorMode(ColorMode.CONTINUOUS_XCOL_MONOCHROME, geneName);
                              setSelectedColor('color');
                              if (!xColMonochrome[geneName]) {
                                const color = chroma.random().rgba();
                                setXColMonochrome({
                                  [geneName]: color,
                                });
                              }
                            }
                          }
                        }}
                      >
                        <Menu.Item key="1">color maps</Menu.Item>
                        <Menu.Item key="2">single color</Menu.Item>
                      </Menu>
                    }
                    trigger={['click']}
                  >
                    <Button
                      size="small"
                      type={colorActive ? 'primary' : 'text'}
                      onClick={(e: any) => {
                        e.stopPropagation();
                        if (colorActive) {
                          updateColorMode(ColorMode.NO_COLOR, null);
                          setSelectedColor('');
                        }
                      }}
                      icon={<BgColorsOutlined />}
                      style={{
                        fontSize: '1em',
                      }}
                    />
                  </Dropdown>
                </Col>
                <Col>
                  <Button
                    size="small"
                    type={expanded ? 'primary' : 'text'}
                    icon={<ExpandAltOutlined />}
                    onClick={() => {
                      setExpanded(!expanded);
                    }}
                    style={{
                      fontSize: '1em',
                    }}
                  />
                </Col>
              </Row>
            }
          >
            <Button
              size="small"
              type="text"
              style={{
                fontSize: '1em',
              }}
              icon={<EllipsisOutlined />}
            />
          </Popover>
        </Col>
      </Row>
      {expanded && (
        <BrushableHistogram
          field={geneName}
          isColorAndMarkerAccessor={
            colorMode === ColorMode.CONTINUOUS_XCOL && colorKey === geneName
          }
          isGeneSetSummary={false}
          isTopGeneSetSummary={false}
          zebra={false}
          isObs={false}
          mini={false}
          hideAnno={false}
          loading={loading}
          setLoading={setLoading}
        />
      )}
    </>
  );
};

const { Panel } = Collapse;

const GenesetHeader = (props) => {
  const { genesetName, expanded, onClick, colorActive, colorArray, color, loading } = props;
  const {
    updateColorMode,
    xColAvgMonochrome,
    setXColAvgMonochrome,
    geneColorList,
    setGeneColorList,
    changeInterpolator,
  } = useModel('cellSelect');
  const [selectedColor, setSelectedColor] = useState('');

  const changeColor = (value: any, key: string) => {
    setXColAvgMonochrome({
      [key]: [value.rgb.r, value.rgb.g, value.rgb.b, value.rgb.a],
    });
  };

  function copyLongName(textToCopy) {
    writeToClipboard(textToCopy)
      .then(() => {
        message.success('text copied');
      })
      .catch(() => {
        console.error('text cannot be copied');
      });
  }

  return (
    <Row
      style={{
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <Col onClick={onClick} span={8}>
        <span
          style={{
            fontSize: '0.8em',
            marginRight: '1vw',
          }}
          title={genesetName}
        >
          <CopyOutlined
            onClick={(e) => {
              e.stopPropagation();
              copyLongName(genesetName);
            }}
          />
          {''}
          {cutString(genesetName, 10)}
          {expanded ? <DownOutlined /> : <RightOutlined />}
        </span>
      </Col>
      <Col flex={1} />
      <Col flex={1} />
      <Col
        style={{
          visibility: colorActive ? 'visible' : 'hidden',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {selectedColor === 'brush' && (
          <Popover
            placement="bottomLeft"
            content={
              <div
                style={{ width: '70px', height: '100px', overflow: 'auto' }}
                onClick={(e) => e.stopPropagation()}
              >
                {colorArray.map((item: any) => {
                  return <ColorBand AlternativeColorBand={item} key={item} />;
                })}
              </div>
            }
            trigger="click"
          >
            <Button
              size="small"
              type="text"
              onClick={(e: any) => {
                e.stopPropagation();
              }}
              icon={<FormatPainterOutlined />}
              style={{
                fontSize: '1em',
                marginRight: '0.1vw',
              }}
            />
          </Popover>
        )}
        {selectedColor === 'brush' && (
          <Popover
            placement="right"
            trigger="click"
            content={
              <ChromePicker
                disableAlpha
                color={geneColorList[0]}
                onClick={(e) => e.stopPropagation()}
                onChange={(color: any) => {
                  geneColorList[0] = `rgba(${color.rgb.r},${color.rgb.g}, ${color.rgb.b}, ${color.rgb.a})`;
                  setGeneColorList([...geneColorList]);
                  const colorScaleFunction = d3
                    .scaleLinear()
                    .domain([0, 0.5, 1]) // Define the positions of the three colors here
                    .range(geneColorList);
                  changeInterpolator(colorScaleFunction);
                }}
              />
            }
          >
            <Button
              size="small"
              type="text"
              onClick={(e: any) => {
                e.stopPropagation();
              }}
              style={{
                height: 10,
                fontSize: '1em',
                marginRight: '0.1vw',
                backgroundColor: geneColorList[0],
              }}
            />
          </Popover>
        )}
        {selectedColor === 'brush' && (
          <Popover
            placement="right"
            trigger="click"
            content={
              <ChromePicker
                disableAlpha
                color={geneColorList[1]}
                onClick={(e) => e.stopPropagation()}
                onChange={(color: any) => {
                  geneColorList[1] = `rgba(${color.rgb.r},${color.rgb.g}, ${color.rgb.b}, ${color.rgb.a})`;
                  setGeneColorList([...geneColorList]);
                  const colorScaleFunction = d3
                    .scaleLinear()
                    .domain([0, 0.5, 1]) // Define the positions of the three colors here
                    .range(geneColorList);
                  changeInterpolator(colorScaleFunction);
                }}
              />
            }
          >
            <Button
              size="small"
              type="text"
              onClick={(e: any) => {
                e.stopPropagation();
              }}
              style={{
                height: 10,
                fontSize: '1em',
                marginRight: '0.1vw',
                backgroundColor: geneColorList[1],
              }}
            />
          </Popover>
        )}
        {selectedColor === 'brush' && (
          <Popover
            placement="right"
            trigger="click"
            content={
              <ChromePicker
                disableAlpha
                color={geneColorList[2]}
                onClick={(e) => e.stopPropagation()}
                onChange={(color: any) => {
                  geneColorList[2] = `rgba(${color.rgb.r},${color.rgb.g}, ${color.rgb.b}, ${color.rgb.a})`;
                  setGeneColorList([...geneColorList]);
                  const colorScaleFunction = d3
                    .scaleLinear()
                    .domain([0, 0.5, 1]) // Define the positions of the three colors here
                    .range(geneColorList);
                  changeInterpolator(colorScaleFunction);
                }}
              />
            }
          >
            <Button
              size="small"
              type="text"
              onClick={(e: any) => {
                e.stopPropagation();
              }}
              style={{
                height: 10,
                fontSize: '1em',
                marginRight: '0.1vw',
                backgroundColor: geneColorList[2],
              }}
            />
          </Popover>
        )}
        {selectedColor === '' ||
          (selectedColor === 'color' && (
            <Button
              size="small"
              type="text"
              onClick={(e: any) => {
                e.stopPropagation();
              }}
              icon={<FormatPainterOutlined />}
              style={{
                fontSize: '1em',
                visibility: 'hidden',
                marginRight: '0.1vw',
              }}
            />
          ))}
        {selectedColor === '' ||
          (selectedColor === 'color' && (
            <Button
              size="small"
              type="text"
              onClick={(e: any) => {
                e.stopPropagation();
              }}
              icon={<FormatPainterOutlined />}
              style={{
                fontSize: '1em',
                visibility: 'hidden',
                marginRight: '0.1vw',
              }}
            />
          ))}
        {selectedColor === 'color' && (
          <Popover
            placement="right"
            trigger="click"
            content={
              <ChromePicker
                disableAlpha
                color={color}
                onClick={(e: any) => {
                  e.stopPropagation();
                }}
                onChange={(color: any) => changeColor(color, genesetName)}
              />
            }
          >
            <Button
              size="small"
              style={{
                // borderRadius: '50%',
                cursor: 'pointer',
                backgroundColor: color,
                height: 10,
                marginRight: '0.1vw',
              }}
              onClick={(e) => {
                e.stopPropagation();
              }}
              icon={<FormatPainterOutlined style={{ visibility: 'hidden' }} />}
            />
          </Popover>
        )}
        {selectedColor === '' && (
          <Button
            size="small"
            type="text"
            onClick={(e: any) => {
              e.stopPropagation();
            }}
            icon={<FormatPainterOutlined />}
            style={{
              fontSize: '1em',
              visibility: 'hidden',
              marginRight: '0.1vw',
            }}
          />
        )}
        {selectedColor === '' && (
          <Button
            size="small"
            type="text"
            onClick={(e: any) => {
              e.stopPropagation();
            }}
            icon={<FormatPainterOutlined />}
            style={{
              fontSize: '1em',
              visibility: 'hidden',
              marginRight: '0.1vw',
            }}
          />
        )}
        {selectedColor === '' && (
          <Button
            size="small"
            type="text"
            onClick={(e: any) => {
              e.stopPropagation();
            }}
            icon={<FormatPainterOutlined />}
            style={{
              fontSize: '1em',
              visibility: 'hidden',
              marginRight: '0.1vw',
            }}
          />
        )}
      </Col>
      <Col style={{ visibility: colorActive ? 'visible' : 'hidden' }} />
      <Col>
        {loading ? (
          // <div
          //   style={{
          //     height: mini ? HEIGHT_MINI : HEIGHT,
          //   }}
          // >
          <Button size="small" loading type="primary" />
        ) : (
          // </div>
          <Dropdown
            overlay={
              <Menu
                onClick={(e: any) => {
                  const { domEvent, key } = e;
                  domEvent.stopPropagation();
                  if (key === '1') {
                    // openSaveModal();
                    if (colorActive) {
                      updateColorMode(ColorMode.NO_COLOR, null);
                      setSelectedColor('');
                    } else {
                      updateColorMode(ColorMode.CONTINUOUS_X_COL_AVG, genesetName);
                      setGeneColorList(['rgb(110,64,170)', 'rgb(26,199,194)', 'rgb(175,240,91)']);
                      const colorScaleFunction = d3
                        .scaleLinear()
                        .domain([0, 0.5, 1]) // Define the positions of the three colors here
                        .range(['rgb(110,64,170)', 'rgb(26,199,194)', 'rgb(175,240,91)']);
                      changeInterpolator(colorScaleFunction);
                      setSelectedColor('brush');
                    }
                  } else if (key === '2') {
                    // openSaveAutoModal();
                    if (colorActive) {
                      updateColorMode(ColorMode.NO_COLOR, null);
                      setSelectedColor('');
                    } else {
                      updateColorMode(ColorMode.CONTINUOUS_X_COL_AVG_MONOCHROME, genesetName);
                      setSelectedColor('color');
                      if (!xColAvgMonochrome[genesetName]) {
                        const color = chroma.random().rgba();
                        setXColAvgMonochrome({
                          [genesetName]: color,
                        });
                      }
                    }
                  }
                }}
              >
                <Menu.Item key="1">color maps</Menu.Item>
                <Menu.Item key="2">single color</Menu.Item>
              </Menu>
            }
            trigger={['click']}
          >
            <Button
              size="small"
              type={colorActive ? 'primary' : 'text'}
              onClick={(e: any) => {
                e.stopPropagation();
                if (colorActive) {
                  updateColorMode(ColorMode.NO_COLOR, null);
                  setSelectedColor('');
                }
                // else {
                //   updateColorMode(ColorMode.CONTINUOUS_X_COL_AVG, genesetName);
                // }
              }}
              icon={<BgColorsOutlined />}
              style={{
                fontSize: '1em',
              }}
            />
          </Dropdown>
        )}
      </Col>
    </Row>
  );
};

interface GenesetProps {
  genesetName: string;
  color: any;
}

const Geneset = (props: GenesetProps) => {
  const { colorMode, colorKey, genesets, xColMonochrome } = useModel('cellSelect');
  const { genesetName, color } = props;
  const [geneList, setGeneList] = useState<any[]>([]);

  const [expanded, setExpanded] = useState(false);

  const [hideAnno, setHideAnno] = useState(false);

  const [loading, setLoading] = useState<boolean>(false);

  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);
  const [showedGeneList, setShowedGeneList] = useState([] as any);

  const [showedCount, setShowedCount] = useState(50);
  useEffect(() => {
    const geneset = genesets[genesetName];

    const geneNameList = geneset.genes;
    // const geneList: any[] = geneNameList.map((geneName: string) => {
    //   return {
    //     geneName,
    //     description: geneset.genes[geneName],
    //   };
    // });

    setGeneList(geneNameList);
  }, [genesets]);

  const loadMoreData = () => {
    const moreList = [
      ...showedGeneList,
      ...geneList.slice(showedGeneList.length - 1, showedGeneList.length - 1 + 30),
    ];
    setShowedGeneList(moreList);
    setShowedCount(showedCount + 10);
  };

  const getShowedList = () => {
    return geneList.slice(0, showedCount);
  };

  useEffect(() => {
    if (geneList) {
      setShowedGeneList(geneList.slice(0, 30));
    }
  }, [geneList]);

  const [colorArray, setColorArray] = useState([] as any[]);

  useEffect(() => {
    const colorBandList: any[] = [];
    colorBandList.push(
      ['rgb(016,070,128)', 'rgb(183,034,048)', 'rgb(109,001,031)'],
      ['rgb(000,077,067)', 'rgb(148,088,015)', 'rgb(089,050,005)'],
      ['rgb(204,146,165)', 'rgb(78,208,136)', 'rgb(128,159,3)'],
      ['rgb(153,116,158)', 'rgb(154,221,175)', 'rgb(241,187,71)'],
      ['rgb(255,148,0)', 'rgb(34,185,54)', 'rgb(150,138,193)'],
      ['rgb(159,142,189)', 'rgb(238,76,179)', 'rgb(230,164,33)'],
      ['rgb(151,197,79)', 'rgb(49,169,113)', 'rgb(242,115,39)'],
      ['rgb(078,171,144)', 'rgb(238,191,109)', 'rgb(131,064,038)'],
      ['rgb(231,056,071)', 'rgb(168,218,219)', 'rgb(029,053,087)'],
      ['rgb(203,153,126)', 'rgb(253,213,113)', 'rgb(107,112,092)'],
      ['rgb(244,241,222)', 'rgb(060,064,091)', 'rgb(242,204,142)'],
      ['rgb(115,186,214)', 'rgb(002,038,062)', 'rgb(196,050,063)'],
      ['rgb(140,048,074)', 'rgb(033,158,188)', 'rgb(254,183,005)'],
      ['rgb(002,205,191)', 'rgb(249,219,149)', 'rgb(197,168,206)'],
      ['rgb( 167, 65,60)', 'rgb(235,214, 87)', 'rgb(182,183,185)'],
    );
    setColorArray(colorBandList);
  }, []);

  // const [colorActive,setColorActive]=useState('')
  const colorActive =
    (colorMode === ColorMode.CONTINUOUS_X_COL_AVG && colorKey === genesetName) ||
    (colorMode === ColorMode.CONTINUOUS_X_COL_AVG_MONOCHROME && colorKey === genesetName);

  return (
    <div>
      <GenesetHeader
        genesetName={genesetName}
        expanded={expanded}
        onClick={() => {
          setExpanded(!expanded);
        }}
        colorArray={colorArray}
        colorActive={colorActive}
        hideAnno={hideAnno}
        toggleAnno={setHideAnno}
        color={color}
        loading={loading}
        setLoading={setLoading}
      />
      {expanded && (
        <BrushableHistogram
          field={genesetName}
          isColorAndMarkerAccessor={
            colorMode === ColorMode.CONTINUOUS_X_COL_AVG && colorKey === genesetName
          }
          isGeneSetSummary={true}
          isTopGeneSetSummary={false}
          zebra={false}
          isObs={false}
          mini={false}
          hideAnno={hideAnno}
          loading={loading}
          setLoading={setLoading}
        />
      )}
      {expanded && (
        <div
          style={{
            width: '100%',
            height: geneList.length > 30 ? '38vh' : 'auto',
            overflow: 'auto',
          }}
          onScroll={(e: any) => {
            const scrollTop = e.target.scrollTop;
            const childClientHeight = e.target.children[0].clientHeight;
            const clientHeight = e.target.clientHeight;
            if (scrollTop + clientHeight + 20 >= childClientHeight) {
              if (timer) {
                clearTimeout(timer);
              }
              setTimer(
                setTimeout(() => {
                  loadMoreData();
                }, 500),
              );
            }
          }}
          onClick={(e) => {
            e.stopPropagation();
          }}
        >
          {getShowedList().map((gene: any) => {
            const rgba = xColMonochrome[gene.name as string] || [0, 0, 0, 1];
            const color = `rgba(${rgba[0]},${rgba[1]},${rgba[2]},${rgba[3]})`;
            return (
              <Gene
                key={gene.name}
                geneName={gene.name}
                genesetName={genesetName}
                colorArray={colorArray}
                color={color}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

const Genesets = () => {
  const { genesets, xColAvgMonochrome } = useModel('cellSelect');

  const genesetNames = Object.keys(genesets);

  return (
    <>
      <Collapse
        style={{
          width: '100%',
          marginBottom: '10px',
        }}
      >
        <Panel
          key="1"
          header={
            <Row gutter={10}>
              <Col>gene sets</Col>
              <Col flex={1} />
            </Row>
          }
        >
          {genesetNames.map((genesetName: string) => {
            const rgba = xColAvgMonochrome[genesetName as string] || [0, 0, 0, 1];
            const color = `rgba(${rgba[0]},${rgba[1]},${rgba[2]},${rgba[3]})`;
            return <Geneset key={genesetName} genesetName={genesetName} color={color} />;
          })}
        </Panel>
      </Collapse>
    </>
  );
};

export default Genesets;
