import LongTextCut from '@/components/common/longTextCut';
import type { DataCol } from '@/interfaces/col';
import { cellSelectorAdata } from '@/util/anndata';
import { summaryObsCategory } from '@/util/summary';
import { DownOutlined, RightOutlined } from '@ant-design/icons';
import { Button, Col, List, Row } from 'antd';
import React from 'react';

interface CategoryItemProps {
  obsKey: string;
  name: string;
  count: number;
}

// Subset
const CategoryItem = (props: CategoryItemProps) => {
  const { name } = props;

  return (
    <Row
      gutter={5}
      style={{
        height: 30,
        width: '98%',
        paddingRight: 5,
        paddingLeft: '20px',
        backgroundColor: 'rgba(243,243,243,.4)',
      }}
      align="middle"
      justify="space-between"
    >
      <Col>
        <LongTextCut text={name} maxLength={10} />
      </Col>
      <Col flex={1} />
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

const RemovedCategoryItemBox = (props: CategoryItemBoxProps) => {
  const { obsKey } = props;

  const [itemList, setItemList] = React.useState<any[]>([]);

  const [loading, setLoading] = React.useState<boolean>(false);

  const [expanded, setExpanded] = React.useState<boolean>(false);

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
        }}
      >
        <Col>
          <LongTextCut text={obsKey} maxLength={14} />
        </Col>
        <Col flex={1} />

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

RemovedCategoryItemBox.defaultProps = {
  obsKey: 'unamed category',
  // visual: true,
  activated: false,
  // onHiddenAll: () => {},
  // onShowAll: () => {},
  onActivate: () => {},
  onDeactivate: () => {},
};

export default RemovedCategoryItemBox;
