import { ColorMode } from '@/constants/cellSelector';
import { useModel } from 'umi';
import CategoryItemBox from './categoryItemBox';
import { List, Row, Col } from 'antd';
import { useEffect, useState } from 'react';
import { DownOutlined, RightOutlined } from '@ant-design/icons';
import RemovedCategoryItemBox from './removedCategoryBox';

const DataClassification = (props) => {
  const { obsKey, active, categoryKeys, colorKey, onActivate, onDeactivate } = props;

  const [expanded, setExpanded] = useState(false);
  useEffect(() => {
    if (
      (obsKey === 'Unchanged' || obsKey === 'Changed' || obsKey === 'New generated') &&
      categoryKeys.length > 0
    ) {
      setExpanded(true);
    }
  }, [obsKey, categoryKeys]);

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
            fontWeight: '600',
            color: !expanded ? '#000' : '#4F56A8',
            userSelect: 'none',
          }}
        >
          {obsKey} ({categoryKeys.length})
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
        {expanded
          ? categoryKeys.map((categoryKey: string) => {
              if (obsKey === 'Removed') {
                return (
                  <RemovedCategoryItemBox
                    key={categoryKey}
                    obsKey={categoryKey}
                    categoryKey={categoryKey}
                    activated={active && colorKey === categoryKey}
                    onActivate={onActivate}
                    onDeactivate={onDeactivate}
                  />
                );
              }
              return (
                <CategoryItemBox
                  key={categoryKey}
                  obsKey={categoryKey}
                  categoryKey={categoryKey}
                  activated={active && colorKey === categoryKey}
                  onActivate={onActivate}
                  onDeactivate={onDeactivate}
                />
              );
            })
          : ''}
      </Row>
    </>
  );
};

interface CategoryBoxProps {
  categoryKeys: any[];
}

const CategoryBox = (props: CategoryBoxProps) => {
  const { categoryKeys } = props;

  const { updateColorMode, colorMode, colorKey, dataStructureClassification } =
    useModel('cellSelect');
  const [unChangedList, setUnChangedList] = useState<string[]>([]);
  const [changedList, setChangedList] = useState<string[]>([]);
  const [newGenerated, setNewGenerated] = useState<string[]>([]);
  const [removedList, setRemovedList] = useState<string[]>([]);
  useEffect(() => {
    if (dataStructureClassification.obs) {
      const changedList = categoryKeys.filter((value) =>
        dataStructureClassification.obs.changed.includes(value),
      );
      const newGenerated = categoryKeys.filter((value) =>
        dataStructureClassification.obs.new.includes(value),
      );
      const removedList = categoryKeys.filter((value) =>
        dataStructureClassification.obs.deleted.includes(value),
      );
      const unChangedList = categoryKeys.filter((value) => {
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
      setUnChangedList(categoryKeys);
      setChangedList([]);
      setNewGenerated([]);
      setRemovedList([]);
    }
  }, [dataStructureClassification]);

  const onActivate = (key: string) => {
    updateColorMode(ColorMode.CATEGORY_OBS, key);
  };

  const onDeactivate = () => {
    updateColorMode(ColorMode.NO_COLOR, null);
  };
  const active = colorMode === ColorMode.CATEGORY_OBS;

  return (
    <div
      style={{
        height: '48%',
        overflow: 'auto',
      }}
    >
      {/* {categoryKeys.map((categoryKey: string) => {
        return (
          <CategoryItemBox
            key={categoryKey}
            obsKey={categoryKey}
            categoryKey={categoryKey}
            activated={active && colorKey === categoryKey}
            onActivate={onActivate}
            onDeactivate={onDeactivate}
          />
        );
      })} */}

      <List
        split={false}
        bordered={false}
        size="small"
        dataSource={['New generated', 'Changed', 'Unchanged', 'Removed']}
        renderItem={(obsKey: string) => {
          switch (obsKey) {
            case 'New generated': {
              return (
                <DataClassification
                  key={obsKey}
                  obsKey={obsKey}
                  categoryKeys={newGenerated}
                  active={active}
                  colorKey={colorKey}
                  onActivate={onActivate}
                  onDeactivate={onDeactivate}
                />
              );
            }
            case 'Changed': {
              return (
                <DataClassification
                  key={obsKey}
                  obsKey={obsKey}
                  categoryKeys={changedList}
                  active={active}
                  colorKey={colorKey}
                  onActivate={onActivate}
                  onDeactivate={onDeactivate}
                />
              );
            }

            case 'Unchanged': {
              return (
                <DataClassification
                  key={obsKey}
                  obsKey={obsKey}
                  categoryKeys={unChangedList}
                  active={active}
                  colorKey={colorKey}
                  onActivate={onActivate}
                  onDeactivate={onDeactivate}
                />
              );
            }

            case 'Removed': {
              return (
                <DataClassification
                  key={obsKey}
                  obsKey={obsKey}
                  categoryKeys={removedList}
                  active={active}
                  colorKey={colorKey}
                  onActivate={onActivate}
                  onDeactivate={onDeactivate}
                />
              );
            }
            default:
              return (
                <DataClassification
                  key={obsKey}
                  obsKey={obsKey}
                  categoryKeys={categoryKeys}
                  active={active}
                  colorKey={colorKey}
                  onActivate={onActivate}
                  onDeactivate={onDeactivate}
                />
              );
          }
        }}
      />
    </div>
  );
};

export default CategoryBox;
