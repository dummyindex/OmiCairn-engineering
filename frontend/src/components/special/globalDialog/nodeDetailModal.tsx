import { Button, Modal, Spin } from 'antd';
import { useModel } from 'umi';

const BODY_WIDTH = 40;

const titleStyle = {
  marginTop: '1em',
  fontSize: '1.2em',
  fontWeight: '500',
};

export default () => {
  const { nodeId, nodeDetail, loading, error, closeModal } = useModel('nodeDetail');

  const { dictionary } = useModel('localization');

  return (
    <Modal
      open={!!nodeId}
      onCancel={closeModal}
      footer={[
        <Button key="resetToOriginal" type="primary" onClick={closeModal}>
          {dictionary.CLOSE}
        </Button>,
      ]}
      width={`${BODY_WIDTH}vw`}
      bodyStyle={{
        maxHeight: '70vh',
        overflow: 'auto',
      }}
      centered
    >
      {loading && <Spin />}
      {error && <div>error</div>}
      {!loading && !error && nodeDetail && (
        <div>
          <div style={titleStyle}>{dictionary.NAME}</div>
          {nodeDetail?.name || 'Report Node'}
          <div style={titleStyle}>Type</div>
          {nodeDetail?.type}
          <div style={titleStyle}>State</div>
          {nodeDetail?.state}
          <div style={titleStyle}>{dictionary.CREATED_AT}</div>
          {nodeDetail?.createdTime}
          {nodeDetail?.reportModel && (
            <>
              <div style={titleStyle}>LLM Model</div>
              {nodeDetail?.reportModel}
            </>
          )}
        </div>
      )}
    </Modal>
  );
};
