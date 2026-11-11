import { ColorMode } from '@/constants/cellSelector';
import {
  DownOutlined,
  FormatPainterOutlined,
  RightOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { Button, Checkbox, Col, List, Popover, Row, Spin } from 'antd';
import { useEffect, useState } from 'react';
import { ChromePicker } from 'react-color';
import { useModel } from 'umi';
import BrushableHistogram from '../../chart/brushableHistogram';
import { cellSelectorAdata } from '@/util/anndata';
import { DimensionSourceType } from '@/constants/cellSelector';

const ColorBand = (props: any) => {
  const { AlternativeColorBand, obsKey } = props;
  const { setContinuousColorDict, continuousColorDict } = useModel('cellSelect');

  // const colorScale = d3
  //   .scaleLinear()
  //   .domain([0, 0.5, 1]) // Positions of the three color stops
  //   .range(AlternativeColorBand);

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
        continuousColorDict[obsKey] = AlternativeColorBand;
        setContinuousColorDict({ ...continuousColorDict });
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

interface ContinueObsItemProps {
  obsKey: string;
  color: string[];
  active: boolean;
  selected: boolean;
  changeColor: (value: any, index: number, key: string) => void;
  handleSelect: (key: string) => void;
  obsKeyType: string;
}

const ContinueObsItem = (props: ContinueObsItemProps) => {
  const { obsKey, color, active, selected, changeColor, handleSelect, obsKeyType } = props;

  const [expanded, setExpanded] = useState(false);
  const [colorArray, setColorArray] = useState([] as any[]);
  const [loading, setLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(false);
  const { xyzDimensions, setXyzDimensions, dimensionsLoading } = useModel('cellSelect');

  const xActive = xyzDimensions[0]
    ? xyzDimensions[0].dimSource === DimensionSourceType.OBS && xyzDimensions[0].dim === obsKey
    : false;
  const yActive = xyzDimensions[1]
    ? xyzDimensions[1].dimSource === DimensionSourceType.OBS && xyzDimensions[1].dim === obsKey
    : false;
  const zActive = xyzDimensions[2]
    ? xyzDimensions[2].dimSource === DimensionSourceType.OBS && xyzDimensions[2].dim === obsKey
    : false;

  const preloadCol = async () => {
    setLoading(true);
    try {
      await cellSelectorAdata.getObsCol(obsKey);
    } catch (e) {
      setError(true);
    }
    setLoading(false);
  };

  const renderLabel = () => {
    if (error) {
      return <span style={{ color: 'grey' }}>{obsKey}</span>;
    }
    if (loading) {
      return (
        <span>
          <Spin indicator={<LoadingOutlined style={{ fontSize: 16 }} spin />} /> {obsKey}
        </span>
      );
    }
    return (
      <Checkbox
        checked={active && selected}
        onChange={(e: any) => {
          e.stopPropagation();
          handleSelect(obsKey);
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            width: '98%',
          }}
        >
          <div
            style={{
              marginRight: '20px',
              whiteSpace: 'nowrap',
              textOverflow: 'ellipsis',
              overflow: 'hidden',
              width: '100px',
            }}
            title={obsKey}
          >
            {/* {cutString(obsKey, 5)} */}
            {obsKey}
          </div>
          {obsKeyType !== 'Removed' ? (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Col>
                <Button
                  size="small"
                  type={xActive ? 'primary' : 'text'}
                  style={{
                    fontSize: '1em',
                    fontWeight: 'bold',
                  }}
                  loading={dimensionsLoading}
                  icon="x"
                  onClick={() => {
                    if (xActive) {
                      setXyzDimensions([null, xyzDimensions[1], xyzDimensions[2]]);
                    } else {
                      setXyzDimensions([
                        {
                          dimSource: DimensionSourceType.OBS,
                          dim: obsKey,
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
                          dimSource: DimensionSourceType.OBS,
                          dim: obsKey,
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
                          dimSource: DimensionSourceType.OBS,
                          dim: obsKey,
                        },
                      ]);
                    }
                  }}
                />
              </Col>
            </div>
          ) : (
            ''
          )}
        </div>
      </Checkbox>
    );
  };

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
    preloadCol();
  }, []);

  return (
    <>
      <Row
        align="middle"
        justify="space-between"
        style={{
          height: 40,
          paddingLeft: '20px',
          backgroundColor: 'rgba(243,243,243,.4)',
        }}
      >
        <Col span={14}>{renderLabel()}</Col>
        {/* <Col span={2}>
          {obsKeyType !== 'Removed' && (
            <Button
              size="small"
              type={xActive ? 'primary' : 'text'}
              style={{
                fontSize: '1em',
                fontWeight: 'bold',
              }}
              onClick={() => {
                if (xActive) {
                  setXyzDimensions([null, xyzDimensions[1], xyzDimensions[2]]);
                } else {
                  setXyzDimensions([
                    {
                      dimSource: DimensionSourceType.OBS,
                      dim: obsKey,
                    },
                    xyzDimensions[1],
                    xyzDimensions[2],
                  ]);
                }
              }}
            >
              x
            </Button>
          )}
        </Col>
        <Col span={2}>
          {obsKeyType !== 'Removed' && (
            <Button
              size="small"
              type={yActive ? 'primary' : 'text'}
              style={{
                fontSize: '1em',
                fontWeight: 'bold',
              }}
              onClick={() => {
                if (yActive) {
                  setXyzDimensions([xyzDimensions[0], null, xyzDimensions[2]]);
                } else {
                  setXyzDimensions([
                    xyzDimensions[0],
                    {
                      dimSource: DimensionSourceType.OBS,
                      dim: obsKey,
                    },
                    xyzDimensions[2],
                  ]);
                }
              }}
            >
              y
            </Button>
          )}
        </Col>
        <Col span={2}>
          {obsKeyType !== 'Removed' && (
            <Button
              size="small"
              type={zActive ? 'primary' : 'text'}
              style={{
                fontSize: '1em',
                fontWeight: 'bold',
              }}
              onClick={() => {
                if (zActive) {
                  setXyzDimensions([xyzDimensions[0], xyzDimensions[1], null]);
                } else {
                  setXyzDimensions([
                    xyzDimensions[0],
                    xyzDimensions[1],
                    {
                      dimSource: DimensionSourceType.OBS,
                      dim: obsKey,
                    },
                  ]);
                }
              }}
            >
              z
            </Button>
          )}
        </Col> */}
        <Col span={3} />
        <Col span={2}>
          {selected && (
            <Popover
              placement="bottomLeft"
              content={
                <div
                  style={{ width: '70px', height: '100px', overflow: 'auto' }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {colorArray.map((item: any) => {
                    return <ColorBand AlternativeColorBand={item} key={item} obsKey={obsKey} />;
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
        </Col>

        <Col span={1}>
          {selected && (
            <Popover
              placement="right"
              trigger="click"
              content={
                <ChromePicker
                  disableAlpha
                  color={color[0]}
                  onClick={(e) => e.stopPropagation()}
                  onChange={(color: any) => changeColor(color, 0, obsKey)}
                />
              }
            >
              <div
                style={{
                  width: '90%', // Width relative to the parent element
                  height: 12,
                  borderRadius: 5,
                  cursor: 'pointer',
                  backgroundColor: color[0],
                }}
              >
                {''}
              </div>
            </Popover>
          )}
        </Col>
        <Col span={1}>
          {selected && (
            <Popover
              placement="right"
              trigger="click"
              content={
                <ChromePicker
                  disableAlpha
                  color={color[1]}
                  onClick={(e) => e.stopPropagation()}
                  onChange={(color: any) => changeColor(color, 1, obsKey)}
                />
              }
            >
              <div
                style={{
                  width: '90%', // Width relative to the parent element
                  height: 12,
                  borderRadius: 5,
                  cursor: 'pointer',
                  backgroundColor: color[1],
                }}
              >
                {''}
              </div>
            </Popover>
          )}
        </Col>
        <Col span={1}>
          {selected && (
            <Popover
              placement="right"
              trigger="click"
              content={
                <ChromePicker
                  disableAlpha
                  color={color[2]}
                  onClick={(e) => e.stopPropagation()}
                  onChange={(color: any) => changeColor(color, 2, obsKey)}
                />
              }
            >
              <div
                style={{
                  width: '90%', // Width relative to the parent element
                  height: 12,
                  borderRadius: 5,
                  cursor: 'pointer',
                  backgroundColor: color[2],
                }}
              >
                {''}
              </div>
            </Popover>
          )}
        </Col>
        <Col span={2}>
          {!expanded ? (
            <RightOutlined
              onClick={() => {
                setExpanded(true);
              }}
            />
          ) : (
            <DownOutlined
              onClick={() => {
                setExpanded(false);
              }}
            />
          )}
        </Col>
      </Row>
      {expanded && (
        <BrushableHistogram
          field={obsKey}
          isColorAndMarkerAccessor={false}
          isGeneSetSummary={false}
          isObs={true}
          zebra={false}
          mini={false}
          hideAnno={true}
          isTopGeneSetSummary={false}
          loading={isLoading}
          setLoading={setIsLoading}
        />
      )}
    </>
  );
};
const RemovedContinueObsItem = (props) => {
  const { continueObsKey } = props;

  return (
    <>
      <Row
        align="middle"
        justify="space-between"
        style={{
          height: 40,
          paddingLeft: '20px',
          backgroundColor: 'rgba(243,243,243,.4)',
        }}
      >
        <Col span={14}>{continueObsKey}</Col>
        <Col span={4} />
      </Row>
    </>
  );
};

const DataClassification = (props) => {
  const {
    obsKey,
    continuousKeys,
    active,
    isSelected,
    continuousColorDict,
    changeColor,
    handleSelect,
  } = props;

  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (
      (obsKey === 'Unchanged' || obsKey === 'Changed' || obsKey === 'New generated') &&
      continuousKeys.length > 0
    ) {
      setExpanded(true);
    }
  }, [obsKey, continuousKeys]);

  return (
    <>
      <Row
        align="middle"
        justify="space-between"
        style={{
          marginTop: '15px',
          marginBottom: '15px',
        }}
      >
        <Col
          span={14}
          style={{
            fontSize: '14px',
            color: !expanded ? '#000' : '#4F56A8',
            fontWeight: '600',
            userSelect: 'none',
          }}
        >
          {obsKey} ({continuousKeys.length})
        </Col>
        <Col span={4} />
        <Col span={2}>
          {!expanded ? (
            <RightOutlined
              onClick={() => {
                setExpanded(true);
              }}
            />
          ) : (
            <DownOutlined
              style={{ color: '#4F56A8' }}
              onClick={() => {
                setExpanded(false);
              }}
            />
          )}
        </Col>
        {expanded && (
          <div style={{ width: '100%' }}>
            <List
              split={false}
              bordered={false}
              size="small"
              dataSource={continuousKeys}
              renderItem={(continueObsKey: string) => {
                const selected = active && isSelected(continueObsKey);
                const rgba = continuousColorDict[continueObsKey as string] || [
                  'rgba[0, 0, 0, 1]',
                  'rgba[0, 0, 0, 1]',
                  'rgba[0, 0, 0, 1]',
                ];
                const color = rgba;
                if (obsKey === 'Removed') {
                  return <RemovedContinueObsItem continueObsKey={continueObsKey} />;
                }
                return (
                  <ContinueObsItem
                    obsKey={continueObsKey}
                    color={color}
                    active={active}
                    selected={selected}
                    changeColor={changeColor}
                    handleSelect={handleSelect}
                    obsKeyType={obsKey}
                  />
                );
              }}
            />
          </div>
        )}
      </Row>
    </>
  );
};

type ContinueSelectedDict = Record<string, boolean>;

interface ContinueBoxProps {
  continuousKeys: string[];
}

const ContinueBox = (props: ContinueBoxProps) => {
  const { continuousKeys } = props;
  const {
    colorMode,
    updateColorMode,
    colorKey,
    continuousColorDict,
    dataStructureClassification,
    setContinuousColorDict,
  } = useModel('cellSelect');

  const [selectedDict, setSelectedDict] = useState<ContinueSelectedDict>({});
  const [unChangedList, setUnChangedList] = useState<string[]>([]);
  const [changedList, setChangedList] = useState<string[]>([]);
  const [newGenerated, setNewGenerated] = useState<string[]>([]);
  const [removedList, setRemovedList] = useState<string[]>([]);
  useEffect(() => {
    if (dataStructureClassification.obs) {
      const changedList = continuousKeys.filter((value) =>
        dataStructureClassification.obs.changed.includes(value),
      );
      const newGenerated = continuousKeys.filter((value) =>
        dataStructureClassification.obs.new.includes(value),
      );
      const removedList = continuousKeys.filter((value) =>
        dataStructureClassification.obs.deleted.includes(value),
      );
      const unChangedList = continuousKeys.filter((value) => {
        return (
          !changedList.includes(value) &&
          !newGenerated.includes(value) &&
          !removedList.includes(value)
        );
      });
      // console.log('changedList', changedList);
      // console.log('newGenerated', newGenerated);
      // console.log('removedList', removedList);
      // console.log('unChangedList', unChangedList);
      setUnChangedList(unChangedList);
      setChangedList(changedList);
      setNewGenerated(newGenerated);
      setRemovedList(removedList);
    } else {
      setUnChangedList(continuousKeys);
      setChangedList([]);
      setNewGenerated([]);
      setRemovedList([]);
    }
  }, [dataStructureClassification]);

  useEffect(() => {
    if (colorMode !== ColorMode.CONTINUOUS_OBS_MULTIPLE) {
      setSelectedDict({});
    }
  }, [colorMode]);

  useEffect(() => {
    if (colorMode === ColorMode.CONTINUOUS_OBS_MULTIPLE) {
      const selectedDict: ContinueSelectedDict = {};
      (colorKey as string[]).forEach((key: string) => {
        selectedDict[key] = true;
      });
      setSelectedDict(selectedDict);
    }
  }, [colorKey]);

  const changeColor = (value: any, index: number, key: string) => {
    continuousColorDict[key][
      index
    ] = `rgba(${value.rgb.r},${value.rgb.g}, ${value.rgb.b}, ${value.rgb.a})`;
    setContinuousColorDict({
      ...continuousColorDict,
    });
  };

  const active = colorMode === ColorMode.CONTINUOUS_OBS_MULTIPLE;

  const isSelected = (key: string) => {
    return selectedDict[key];
  };

  const handleSelect = async (key: string) => {
    const newSelectedDict = { ...selectedDict };

    if (selectedDict[key]) {
      delete newSelectedDict[key];
    } else {
      newSelectedDict[key] = true;
    }
    setSelectedDict(newSelectedDict);
    updateColorMode(ColorMode.CONTINUOUS_OBS_MULTIPLE, Object.keys(newSelectedDict));
  };

  return (
    <div
      style={{
        height: '50%',
        overflow: 'auto',
      }}
    >
      <List
        split={false}
        bordered={false}
        size="small"
        dataSource={['New generated', 'Changed', 'Unchanged', 'Removed']}
        renderItem={(classification: string) => {
          switch (classification) {
            case 'New generated': {
              return (
                <DataClassification
                  obsKey={classification}
                  continuousKeys={newGenerated}
                  active={active}
                  isSelected={isSelected}
                  continuousColorDict={continuousColorDict}
                  changeColor={changeColor}
                  handleSelect={handleSelect}
                />
              );
            }
            case 'Changed': {
              return (
                <DataClassification
                  obsKey={classification}
                  continuousKeys={changedList}
                  active={active}
                  isSelected={isSelected}
                  continuousColorDict={continuousColorDict}
                  changeColor={changeColor}
                  handleSelect={handleSelect}
                />
              );
            }
            case 'Unchanged': {
              return (
                <DataClassification
                  obsKey={classification}
                  continuousKeys={unChangedList}
                  active={active}
                  isSelected={isSelected}
                  continuousColorDict={continuousColorDict}
                  changeColor={changeColor}
                  handleSelect={handleSelect}
                />
              );
            }

            case 'Removed': {
              return (
                <DataClassification
                  obsKey={classification}
                  continuousKeys={removedList}
                  active={active}
                  isSelected={isSelected}
                  continuousColorDict={continuousColorDict}
                  changeColor={changeColor}
                  handleSelect={handleSelect}
                />
              );
            }
            default:
              return (
                <DataClassification
                  obsKey={classification}
                  continuousKeys={continuousKeys}
                  active={active}
                  isSelected={isSelected}
                  continuousColorDict={continuousColorDict}
                  changeColor={changeColor}
                  handleSelect={handleSelect}
                />
              );
          }
        }}
      />
    </div>
  );
};

export default ContinueBox;
