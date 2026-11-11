import { ColorMode, CellLeftMenu } from '@/constants/cellSelector';
import { DataCol } from '@/interfaces/col';
import { sortCol } from '@/util/colTool';
import { FormatPainterOutlined } from '@ant-design/icons';
import { Checkbox, Col, Divider, List, Popover, Row, Skeleton, Spin, message, Button } from 'antd';
import chroma from 'chroma-js';
import { useEffect, useState } from 'react';
import { ChromePicker } from 'react-color';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useModel } from 'umi';
import * as d3 from 'd3';

const SEGMENT_SIZE = 50;

const generateUniqueRandomColors = (count) => {
  const uniqueColors = new Set();

  while (uniqueColors.size < count) {
    uniqueColors.add(chroma.random().rgba());
  }
  const colorArr = Array.from(uniqueColors).map((item: any) => {
    return `rgba(${item[0]},${item[1]},${item[2]},${item[3]})`;
  });
  return colorArr;
};

const ColorBand = (props: any) => {
  const { AlternativeColorBand, varName } = props;
  const { setGeneColorDict, geneColorDict } = useModel('cellSelect');

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
        // changeInterpolator(AlternativeColorBand);
        geneColorDict[varName] = AlternativeColorBand;
        setGeneColorDict({ ...geneColorDict });
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

const GeneContent = (props) => {
  const { menuSelected, dataStructure } = props;
  const {
    searchKey,
    colorMode,
    colorKey,
    geneColorDict,
    setGeneColorDict,
    updateColorMode,
    changeInterpolator,
  } = useModel('cellSelect');

  // const [geneMarker, setGeneMarker] = useState(ChartsMarkerType.CIRCLES);
  const [geneList, setGeneList] = useState(new DataCol() as DataCol);
  const [loading, setLoading] = useState(true);
  const [showedCount, setShowedCount] = useState(SEGMENT_SIZE);

  const filteredGeneList = !searchKey
    ? geneList
    : geneList.filter((varName: string) =>
        varName.toUpperCase().includes(searchKey.trim().toUpperCase()),
      );

  const loadMoreData = () => {
    setShowedCount(showedCount + SEGMENT_SIZE);
  };

  const loadGeneList = async () => {
    setLoading(true);
    try {
      const varNames = dataStructure.var_names;
      const geneList: DataCol = new DataCol(varNames);
      // const geneListCopy = [...varNames];
      setShowedCount(SEGMENT_SIZE);
      setGeneList(sortCol(geneList, 'sortAsc'));
    } catch (e: any) {
      message.error(e.message);
    } finally {
      setLoading(false);
    }
  };
  const [colorArray, setColorArray] = useState([] as any[]);

  const handleSelect = (key: string) => {
    if (colorMode !== ColorMode.CONTINUOUS_X_COL_MULTIPLE) {
      if (!geneColorDict[key]) {
        const colorArr: any[] = generateUniqueRandomColors(3);
        setGeneColorDict({
          ...geneColorDict,
          [key]: colorArr,
        });
      }
      updateColorMode(ColorMode.CONTINUOUS_X_COL_MULTIPLE, [key]);
      return;
    }
    let selectedKeys = colorKey as string[];
    selectedKeys = [...selectedKeys];
    if (selectedKeys.includes(key)) {
      selectedKeys = selectedKeys.filter((item: string) => item !== key);
      delete geneColorDict[key];
      setGeneColorDict({
        ...geneColorDict,
      });

      updateColorMode(ColorMode.CONTINUOUS_X_COL_MULTIPLE, selectedKeys);
    } else {
      if (!geneColorDict[key]) {
        const colorArr: any[] = generateUniqueRandomColors(3);
        setGeneColorDict({
          ...geneColorDict,
          [key]: colorArr,
        });
      }
      selectedKeys.push(key);
      updateColorMode(ColorMode.CONTINUOUS_X_COL_MULTIPLE, selectedKeys);
    }
  };
  // const onChangeMarker = (value: any) => {
  //   setGeneMarker(value);
  // };

  useEffect(() => {
    if (menuSelected == CellLeftMenu.GENE) {
      loadGeneList();
    }
  }, [menuSelected]);

  useEffect(() => {
    const colorBandList: any[] = [];

    colorBandList.push(
      ['rgba(016,070,128,1)', 'rgba(183,034,048,1)', 'rgba(109,001,031,1)'],
      ['rgba(000,077,067,1)', 'rgba(148,088,015,1)', 'rgba(089,050,005,1)'],
      ['rgba(204,146,165,1)', 'rgba(78,208,136,1)', 'rgba(128,159,3,1)'],
      ['rgba(153,116,158,1)', 'rgba(154,221,175,1)', 'rgba(241,187,71,1)'],
      ['rgba(255,148,0,1)', 'rgba(34,185,54,1)', 'rgba(150,138,193,1)'],
      ['rgba(159,142,189,1)', 'rgba(238,76,179,1)', 'rgba(230,164,33,1)'],
      ['rgba(151,197,79,1)', 'rgba(49,169,113,1)', 'rgba(242,115,39,1)'],
      ['rgba(078,171,144,1)', 'rgba(238,191,109,1)', 'rgba(131,064,038,1)'],
      ['rgba(231,056,071,1)', 'rgba(168,218,219,1)', 'rgba(029,053,087,1)'],
      ['rgba(203,153,126,1)', 'rgba(253,213,113,1)', 'rgba(107,112,092,1)'],
      ['rgba(244,241,222,1)', 'rgba(060,064,091,1)', 'rgba(242,204,142,1)'],
      ['rgba(115,186,214,1)', 'rgba(002,038,062,1)', 'rgba(196,050,063,1)'],
      ['rgba(140,048,074,1)', 'rgba(033,158,188,1)', 'rgba(254,183,005,1)'],
      ['rgba(002,205,191,1)', 'rgba(249,219,149,1)', 'rgba(197,168,206,1)'],
      ['rgba( 167, 65,60,1)', 'rgba(235,214, 87,1)', 'rgba(182,183,185,1)'],
    );

    setColorArray(colorBandList);
  }, []);

  // useEffect(() => {
  //   if (colorMode === ColorMode.CONTINUOUS_X_COL_MULTIPLE) {
  //     const selectedDict: GeneSelectedDict = {};
  //     (colorKey as string[]).forEach((key: string) => {
  //       selectedDict[key] = true;
  //     });
  //     // setSelectedDict(selectedDict);
  //   }
  // }, [colorKey]);

  const getShowedList = () => {
    if (searchKey) {
      return filteredGeneList.slice(0, showedCount);
    } else {
      return filteredGeneList.slice(0, showedCount);
    }
  };

  const active = colorMode === ColorMode.CONTINUOUS_X_COL_MULTIPLE;

  return (
    <>
      {loading && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'stretch',
            height: '100%',
          }}
          id="scrollableDiv"
        >
          <Spin size="large" />
        </div>
      )}
      {!loading && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-start',
            alignItems: 'stretch',
            height: '100%',
            overflow: 'auto',
          }}
          id="scrollableDiv"
        >
          <InfiniteScroll
            dataLength={showedCount}
            next={loadMoreData}
            hasMore={showedCount < filteredGeneList.getLength()}
            loader={<Skeleton avatar paragraph={{ rows: 1 }} active />}
            endMessage={<Divider plain>It is all, nothing more</Divider>}
            scrollableTarget="scrollableDiv"
          >
            <List
              style={{
                width: '100%',
              }}
              split={false}
              bordered={false}
              size="small"
              dataSource={getShowedList().getElements()}
              renderItem={(varName: string) => {
                const selected = active && colorKey?.includes(varName);

                // const rgba = geneColorDict[varName as string] || [0, 0, 0, 1];
                // const geneColor = `rgba(${rgba[0]},${rgba[1]},${rgba[2]},${rgba[3]})`;
                return (
                  <Row align="middle" justify="space-between">
                    <Col>
                      <Checkbox
                        checked={selected}
                        style={{
                          margin: '10px 0',
                        }}
                        onChange={(e: any) => {
                          e.stopPropagation();
                          handleSelect(varName);
                        }}
                      >
                        {varName}
                      </Checkbox>
                    </Col>
                    <Col>
                      {/* {selected && (
                        <Popover
                          placement="right"
                          trigger="click"
                          content={
                            <ChromePicker disableAlpha color={geneColor} onChange={changeColor} />
                          }
                        >
                          <div
                            style={{
                              marginRight: 5,
                              width: 41,
                              height: 12,
                              borderRadius: 5,
                              cursor: 'pointer',
                              backgroundColor: geneColor,
                            }}
                          >
                            {''}
                          </div>
                        </Popover>
                      )} */}{' '}
                      {selected && (
                        <Popover
                          placement="bottomLeft"
                          content={
                            <div
                              style={{ width: '70px', height: '100px', overflow: 'auto' }}
                              onClick={(e) => e.stopPropagation()}
                            >
                              {colorArray.map((item: any) => {
                                return (
                                  <ColorBand
                                    AlternativeColorBand={item}
                                    key={item}
                                    varName={varName}
                                  />
                                );
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
                      {selected && (
                        <Popover
                          placement="right"
                          trigger="click"
                          content={
                            <ChromePicker
                              disableAlpha
                              color={geneColorDict[varName][0]}
                              onClick={(e) => e.stopPropagation()}
                              onChange={(color: any) => {
                                geneColorDict[
                                  varName
                                ][0] = `rgba(${color.rgb.r},${color.rgb.g}, ${color.rgb.b}, ${color.rgb.a})`;
                                setGeneColorDict({ ...geneColorDict });
                                const colorScaleFunction = d3
                                  .scaleLinear()
                                  .domain([0, 0.5, 1]) // Positions of the three color stops
                                  .range(geneColorDict[varName]);
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
                              backgroundColor: geneColorDict[varName][0],
                            }}
                          />
                        </Popover>
                      )}
                      {selected && (
                        <Popover
                          placement="right"
                          trigger="click"
                          content={
                            <ChromePicker
                              disableAlpha
                              color={geneColorDict[varName][1]}
                              onClick={(e) => e.stopPropagation()}
                              onChange={(color: any) => {
                                geneColorDict[
                                  varName
                                ][1] = `rgba(${color.rgb.r},${color.rgb.g}, ${color.rgb.b}, ${color.rgb.a})`;
                                setGeneColorDict({ ...geneColorDict });
                                const colorScaleFunction = d3
                                  .scaleLinear()
                                  .domain([0, 0.5, 1]) // Positions of the three color stops
                                  .range(geneColorDict[varName]);
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
                              backgroundColor: geneColorDict[varName][1],
                            }}
                          />
                        </Popover>
                      )}
                      {selected && (
                        <Popover
                          placement="right"
                          trigger="click"
                          content={
                            <ChromePicker
                              disableAlpha
                              color={geneColorDict[varName][2]}
                              onClick={(e) => e.stopPropagation()}
                              onChange={(color: any) => {
                                geneColorDict[
                                  varName
                                ][2] = `rgba(${color.rgb.r},${color.rgb.g}, ${color.rgb.b}, ${color.rgb.a})`;
                                setGeneColorDict({ ...geneColorDict });
                                const colorScaleFunction = d3
                                  .scaleLinear()
                                  .domain([0, 0.5, 1]) // Positions of the three color stops
                                  .range(geneColorDict[varName]);
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
                              backgroundColor: geneColorDict[varName][2],
                            }}
                          />
                        </Popover>
                      )}
                    </Col>
                  </Row>
                );
              }}
            />
          </InfiniteScroll>
        </div>
      )}
    </>
  );
};

export default GeneContent;
