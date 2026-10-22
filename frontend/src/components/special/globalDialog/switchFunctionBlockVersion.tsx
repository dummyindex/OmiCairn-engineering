import { Modal, List, Row, Col } from 'antd';
import type { FunctionBlockVersion } from '@/interfaces/functionBlock';

import { useModel } from 'umi';

const SwitchFunctionBlockVersion = () => {
  const { switchedFunctionBlockId, versionList, currentVersionId, loading, close, switchVersion } =
    useModel('functionBlockVersionSwitch');

  const renderFn = (item: FunctionBlockVersion, index: number) => {
    return (
      <Row
        key={item.id}
        style={{
          borderBottom: index !== versionList.length - 1 ? '1px solid #f0f0f0' : 'none',
          padding: '10px 0',
          fontSize: '14px',
        }}
      >
        <Col
          span={3}
          style={{
            fontWeight: 'bold',
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'flex-start',
            alignItems: 'center',
          }}
        >
          {item.name}
        </Col>
        <Col span={15}>{item.description}</Col>
        <Col
          span={4}
          style={{
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          {item.createdTime}
        </Col>
        <Col
          span={2}
          style={{
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'space-around',
            alignItems: 'center',
          }}
        >
          {currentVersionId + '' === item.id + '' ? (
            <span style={{ color: 'green' }}>Current</span>
          ) : (
            <a
              onClick={() => {
                switchVersion(item.id);
              }}
            >
              Switch
            </a>
          )}
        </Col>
      </Row>
    );
  };

  return (
    <Modal
      title="Switch Function Block Version"
      open={!!switchedFunctionBlockId || switchedFunctionBlockId === 0}
      onOk={() => {
        close();
      }}
      onCancel={() => {
        close();
      }}
      showCancelButton={false}
      width="60vw"
      centered
      bodyStyle={{ maxHeight: '60vh', overflow: 'auto' }}
      cancelButtonProps={{ style: { display: 'none' } }}
      confirmLoading={loading}
    >
      <Row
        style={{
          borderBottom: '1px solid #f0f0f0',
          padding: '10px 0',
          fontSize: '14px',
          fontWeight: 'bold',
        }}
      >
        <Col span={3}>Name</Col>
        <Col span={15}>Description</Col>
        <Col
          span={4}
          style={{
            textAlign: 'center',
          }}
        >
          CreatedTime
        </Col>
        <Col
          span={2}
          style={{
            textAlign: 'center',
          }}
        >
          Action
        </Col>
      </Row>
      {!!switchedFunctionBlockId && !!versionList && (
        <List
          // header={<FunctionBlockVersionListHeader />}
          itemLayout="horizontal"
          loading={loading}
          dataSource={versionList}
          renderItem={renderFn}
          split={true}
        />
      )}
    </Modal>
  );
};

export default SwitchFunctionBlockVersion;
