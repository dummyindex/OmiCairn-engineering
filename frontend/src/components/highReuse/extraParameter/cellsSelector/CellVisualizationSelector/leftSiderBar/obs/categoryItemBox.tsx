import LongTextCut from '@/components/common/longTextCut';
import { ColorMode } from '@/constants/cellSelector';
import type { DataCol } from '@/interfaces/col';
import { cellSelectorAdata } from '@/util/anndata';
import { cellSelectorFilter as cellFilter } from '@/util/cellFilter';
import { summaryObsCategory } from '@/util/summary';
import {
  BgColorsOutlined,
  DownOutlined,
  EyeFilled,
  EyeInvisibleFilled,
  FormatPainterOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { Button, Col, List, Popover, Row } from 'antd';
import React, { useEffect, useState } from 'react';
import { ChromePicker } from 'react-color';
import { useModel } from 'umi';

const ColorBand = (props: any) => {
  const { AlternativeColorBand } = props;
  const { updateColor } = useModel('cellSelect');
  return (
    <div
      style={{
        height: 15,
        width: '100%',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'flex-start',
        alignItems: 'stretch',
        marginTop: '5px',
        marginBottom: '5px',
      }}
      onClick={(e) => {
        e.stopPropagation();
        updateColor(AlternativeColorBand);
      }}
    >
      {AlternativeColorBand.map((bandItem) => {
        return (
          <div
            key={bandItem}
            style={{
              height: '100%',
              width: `8%`,
              backgroundColor: bandItem,
            }}
          />
        );
      })}
    </div>
  );
};

interface OtherCategoryRenderColorBandProps {
  obsKey: string;
  name: string;
}

const OtherCategoryRenderColorBand = (props: OtherCategoryRenderColorBandProps) => {
  const { categoryColorDict, colorKey } = useModel('cellSelect');
  const { obsKey, name } = props;

  const [colorBandList, setColorBandList] = useState<any[]>([]);

  const loadColorBandList = async () => {
    const bandItemDict = {};
    const [coloredCol, currentCol] = await Promise.all([
      cellSelectorAdata.getObsCol(colorKey as string),
      cellSelectorAdata.getObsCol(obsKey),
    ]);
    if (!coloredCol || !currentCol) {
      throw new Error('coloredCol or currentCol is null');
    }
    let totalCount = 0;
    currentCol.forEach((value: any, index: number) => {
      if (value === name) {
        totalCount += 1;
        if (!bandItemDict[coloredCol.at(index)]) {
          bandItemDict[coloredCol.at(index)] = 1;
        } else {
          bandItemDict[coloredCol.at(index)] += 1;
        }
      }
    });
    const bandItemNameList = Object.keys(bandItemDict);
    bandItemNameList.sort();
    const bandItemList = bandItemNameList.map((bandItemName) => {
      return {
        name: bandItemName,
        count: bandItemDict[bandItemName],
        rate: bandItemDict[bandItemName] / totalCount,
        color: categoryColorDict[colorKey as string][bandItemName],
      };
    });
    setColorBandList(bandItemList);
  };

  useEffect(() => {
    loadColorBandList();
  }, [categoryColorDict, colorKey, obsKey, name]);

  return (
    <div
      style={{
        height: 8,
        width: '100%',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'flex-start',
        alignItems: 'stretch',
      }}
    >
      {colorBandList.map((bandItem) => {
        const { name, count, rate, color } = bandItem;
        return (
          <div
            key={name}
            style={{
              height: '100%',
              width: `${rate * 100}%`,
              backgroundColor: `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${color[3]})`,
            }}
            title={`${name}: ${count}`}
          />
        );
      })}
    </div>
  );
};

interface CategoryItemColorSelectorProps {
  color: string;
  onColorChange: (color: any) => void;
}

const CategoryItemColorSelector = (props: CategoryItemColorSelectorProps) => {
  const { color, onColorChange: onColorChangeInParent } = props;
  const onColorChange = (color: any) => {
    onColorChangeInParent(color);
  };
  return (
    <Popover
      placement="right"
      trigger="click"
      content={<ChromePicker color={color} onChange={(color: any) => onColorChange(color)} />}
    >
      <div
        style={{
          height: 12,
          position: 'relative',
          width: '80%',
          borderRadius: 5,
          cursor: 'pointer',
          backgroundColor: color,
        }}
      />
    </Popover>
  );
};

interface CategoryItemProps {
  obsKey: string;
  name: string;
  count: number;
}

// Subset
const CategoryItem = (props: CategoryItemProps) => {
  const {
    cellFilterVersionUuid,
    categoryColorDict,
    setCategoryColorDict,
    setCellFilterVersionUuid,
    colorMode,
    colorKey,
    setHighlightedTable,
  } = useModel('cellSelect');
  const { obsKey, name, count } = props;

  const rgba = categoryColorDict[obsKey][name];
  const color = `rgba(${rgba[0]}, ${rgba[1]}, ${rgba[2]}, ${rgba[3]})`;

  const [visual, setVisual] = React.useState<boolean>(true);

  const onColorChange = (color: any, key: string) => {
    setCategoryColorDict({
      ...categoryColorDict,
      [obsKey]: {
        ...categoryColorDict[obsKey],
        [key]: [color.rgb.r, color.rgb.g, color.rgb.b, color.rgb.a],
      },
    });
  };

  const handleEyeClick = async (e) => {
    e.stopPropagation();
    const categoryCol = await cellSelectorAdata.getObsCol(obsKey);
    if (visual) {
      cellFilter?.maskByCluster(obsKey, name, categoryCol);
    } else {
      cellFilter?.unmaskByCluster(obsKey, name);
    }
    cellFilter?.upgradeVersionUuid();
    setCellFilterVersionUuid(cellFilter?.getVersionUuid());
  };

  const judgeVisual = async () => {
    const visual = cellFilter?.queryByCluster(obsKey, name);
    setVisual(visual);
  };

  useEffect(() => {
    judgeVisual();
  }, [cellFilterVersionUuid]);

  const eyeIcon = visual ? <EyeFilled /> : <EyeInvisibleFilled />;

  const isOtherCategoryRendered = colorMode === ColorMode.CATEGORY_OBS && colorKey !== obsKey;

  const renderColorBand = () => {
    if (isOtherCategoryRendered) {
      return <OtherCategoryRenderColorBand obsKey={obsKey} name={name} />;
    } else {
      return (
        <CategoryItemColorSelector
          color={color}
          onColorChange={(color: any) => onColorChange(color, name)}
        />
      );
    }
  };

  const highlightCells = async () => {
    const obsCol = await cellSelectorAdata.getObsCol(obsKey);
    if (!obsCol) {
      throw new Error('obsCol is null');
    }
    const newHighlightedTable = obsCol.map((obsColValue: any) => {
      return obsColValue === name;
    });

    setHighlightedTable(newHighlightedTable.getElements());
  };

  const unhighlightCells = async () => {
    setHighlightedTable(null);
  };

  return (
    <Row
      gutter={5}
      style={{
        height: 30,
        width: '98%',
        paddingRight: 5,
        // backgroundColor: name === selectCellSetName ? 'rgba(89, 113, 192, 0.16)' : '',
      }}
      align="middle"
      justify="space-between"
      onMouseEnter={highlightCells}
      onMouseLeave={unhighlightCells}
    >
      <Col>
        <Button size="small" type="text" icon={eyeIcon} onClick={handleEyeClick} />
      </Col>
      <Col>
        <LongTextCut text={name} maxLength={10} />
      </Col>
      <Col flex={1} />
      <Col span={isOtherCategoryRendered ? 4 : 2}>{renderColorBand()}</Col>
      <Col
        span={3}
        style={{
          textAlign: 'right',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
      >
        {count}
      </Col>
    </Row>
  );
};

interface CategoryItemBoxProps {
  obsKey: string;
  categoryKey: string;
  // visual: boolean;
  activated: boolean;
  // onHiddenAll?: () => void;
  // onShowAll?: () => void;
  onActivate?: (key: string) => void;
  onDeactivate?: (key: string) => void;
}

const CategoryItemBox = (props: CategoryItemBoxProps) => {
  const { obsKey, activated, categoryKey, onActivate, onDeactivate } = props;

  const { cellFilterVersionUuid, setCellFilterVersionUuid } = useModel('cellSelect');

  const [itemList, setItemList] = React.useState<any[]>([]);

  const [loading, setLoading] = React.useState<boolean>(false);

  const [expanded, setExpanded] = React.useState<boolean>(false);

  const [visual, setVisual] = React.useState<boolean>(true);

  const [colorArray, setColorArray] = useState([] as any[]);

  const initial = async () => {
    setLoading(true);
    try {
      const obsCol: DataCol = await cellSelectorAdata.getObsCol(obsKey);
      const { clusters, cluster2Count } = summaryObsCategory(obsCol);
      const itemList = clusters.map((cluster: string) => {
        return {
          name: cluster,
          count: cluster2Count.get(cluster),
        };
      });
      setItemList(itemList);
    } catch (e) {
      console.log(e);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    initial();
  }, [obsKey]);

  const judgeVisual = async () => {
    const visual = cellFilter?.queryByCategory(categoryKey);
    setVisual(visual);
  };

  useEffect(() => {
    judgeVisual();
  }, [cellFilterVersionUuid]);

  const eyeIcon = visual ? <EyeFilled /> : <EyeInvisibleFilled />;

  const segment = 50;
  const [showedCount, setShowedCount] = React.useState(50);

  const onLoadMore = () => {
    setShowedCount(showedCount + segment);
  };

  const loadMore = () => {
    return (
      <div
        hidden={showedCount >= itemList.length}
        style={{
          textAlign: 'center',
          marginTop: 12,
          height: 32,
          lineHeight: '32px',
        }}
      >
        <Button onClick={onLoadMore}>loading more</Button>
      </div>
    );
  };

  const handleEyeClick = async (e: any) => {
    e.stopPropagation();
    const obsCol = await cellSelectorAdata.getObsCol(categoryKey);
    if (visual) {
      cellFilter?.maskByCategory(categoryKey, obsCol);
    } else {
      cellFilter?.unmaskByCategory(categoryKey);
    }
    cellFilter?.upgradeVersionUuid();
    setCellFilterVersionUuid(cellFilter?.getVersionUuid());
  };

  useEffect(() => {
    const colorBandList: any[] = [];

    colorBandList.push(
      [
        'rgb(016,070,128)',
        'rgb(049,124,183)',
        'rgb(109,173,209)',
        'rgb(182,215,232)',
        'rgb(233,241,244)',
        'rgb(251,227,213)',
        'rgb(246,178,147)',
        'rgb(220,109,087)',
        'rgb(183,034,048)',
        'rgb(109,001,031)',
      ],
      [
        'rgb(000,077,067)',
        'rgb(026,126,118)',
        'rgb(093,179,169)',
        'rgb(169,221,213)',
        'rgb(228,241,239)',
        'rgb(245,236,210)',
        'rgb(228,203,142)',
        'rgb(197,142,060)',
        'rgb(148,088,015)',
        'rgb(089,050,005)',
      ],
      [
        'rgb(204,146,165)',
        'rgb(178,138,174)',
        'rgb(180,167,233)',
        'rgb(92,188,229)',
        'rgb(77,134,158)',
        'rgb(78,208,136)',
        'rgb(87,198,99)',
        'rgb(205,232,107)',
        'rgb(148,217,100)',
        'rgb(128,159,3)',
      ],
      [
        'rgb(153,116,158)',
        'rgb(207,169,234)',
        'rgb(246,222,246)',
        'rgb(215,230,245)',
        'rgb(194,244,207)',
        'rgb(154,221,175)',
        'rgb(149,183,207)',
        'rgb(60,154,104)',
        'rgb(235,140,51)',
        'rgb(241,187,71)',
      ],
      [
        'rgb(255,148,0)',
        'rgb(192,192,192)',
        'rgb(233,33,55)',
        'rgb(148,214,215)',
        'rgb(53,115,180)',
        'rgb(34,185,54)',
        'rgb(182,144,41)',
        'rgb(28,179,233)',
        'rgb(91,177,54)',
        'rgb(150,138,193)',
      ],
      [
        'rgb(159,142,189)',
        'rgb(87,144,173)',
        'rgb(132,172,93)',
        'rgb(133,162,205)',
        'rgb(211,128,138)',
        'rgb(238,76,179)',
        'rgb(172,172,172)',
        'rgb(191,30,121)',
        'rgb(63,144,55)',
        'rgb(230,164,33)',
      ],
      [
        'rgb(151,197,79)',
        'rgb(44,175,31)',
        'rgb(7,133,70)',
        'rgb(59,148,93)',
        'rgb(95,178,118)',
        'rgb(49,169,113)',
        'rgb(99,170,82)',
        'rgb(185,221,195)',
        'rgb(70,126,189)',
        'rgb(242,115,39)',
      ],
    );

    setColorArray(colorBandList);
  }, []);

  return (
    <>
      <Row
        gutter={5}
        align="middle"
        justify="space-between"
        onClick={() => setExpanded(!expanded)}
        style={{
          height: 50,
          cursor: 'pointer',
          width: '98%',
          paddingLeft: '20px',
          backgroundColor: 'rgba(243,243,243,.4)',
        }}
      >
        <Col>
          <Button size="small" type="text" icon={eyeIcon} onClick={handleEyeClick} />
        </Col>
        <Col>
          <LongTextCut text={obsKey} maxLength={10} />
        </Col>
        <Col flex={1} />
        {activated && (
          <Col>
            <Popover
              placement="bottomLeft"
              content={
                <div
                  style={{ width: '100px', height: '100px', overflow: 'auto' }}
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
                loading={loading}
                type="default"
                icon={<FormatPainterOutlined />}
                onClick={(e: any) => {
                  e.stopPropagation();
                }}
              />
            </Popover>
          </Col>
        )}

        <Col>
          <Button
            size="small"
            loading={loading}
            type={activated ? 'primary' : 'default'}
            icon={<BgColorsOutlined />}
            onClick={(e: any) => {
              e.stopPropagation();
              const fn = activated ? onDeactivate : onActivate;
              if (!!fn) {
                fn(categoryKey);
              }
            }}
          />
        </Col>
        <Col span={2}>{expanded ? <DownOutlined /> : <RightOutlined />}</Col>
      </Row>
      {expanded && (
        <List
          loadMore={loadMore()}
          loading={loading}
          size="small"
          style={{ width: '100%' }}
          dataSource={itemList.slice(0, showedCount)}
          renderItem={(item: any) => {
            const { name, count } = item;
            return <CategoryItem obsKey={obsKey} name={name} count={count} />;
          }}
        />
      )}
    </>
  );
};

CategoryItemBox.defaultProps = {
  obsKey: 'unamed category',
  // visual: true,
  activated: false,
  // onHiddenAll: () => {},
  // onShowAll: () => {},
  onActivate: () => {},
  onDeactivate: () => {},
};

export default CategoryItemBox;
