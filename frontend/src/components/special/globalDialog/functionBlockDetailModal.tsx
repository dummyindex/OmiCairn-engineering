import { Modal, Button, Spin, Image } from 'antd';
import { useModel } from 'umi';

const BODY_WIDTH = 40;

const titleStyle = {
  marginTop: '1em',
  fontSize: '1.2em',
  fontWeight: '500',
};

export default () => {
  const { functionBlockId, functionBlockDetail, loading, error, closeModal } =
    useModel('functionBlockDetail');

  const { dictionary } = useModel('localization');

  return (
    <Modal
      open={!!functionBlockId}
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
      {!loading && !error && functionBlockDetail && (
        <div>
          <div style={titleStyle}>{dictionary.NAME}</div>
          {functionBlockDetail?.name}
          <div style={titleStyle}>{dictionary.CURRENT_VERSION}</div>
          {functionBlockDetail?.currentVersionName}
          <div style={titleStyle}>{dictionary.SOURCE}</div>
          {functionBlockDetail?.source}
          <div style={titleStyle}>{dictionary.CREATED_AT}</div>
          {functionBlockDetail?.createdTime}
          <div style={titleStyle}>{dictionary.LINK}</div>
          <a href={functionBlockDetail?.link || '#'} target="_blank" rel="noreferrer">
            {functionBlockDetail?.link || '#'}
          </a>
          <div style={titleStyle}>{dictionary.DESCRIPTION}</div>
          {functionBlockDetail?.description}
          {(functionBlockDetail?.previewImages?.length || 0) > 0 && (
            <div style={titleStyle}>{dictionary.PREVIEW_IMAGE}</div>
          )}
          <Image.PreviewGroup>
            {functionBlockDetail?.previewImages?.map((preview) => (
              <>
                <Image
                  key={preview}
                  src={preview}
                  style={{
                    width: `${BODY_WIDTH - 4}vw`,
                    height: 'auto',
                  }}
                />
                <div style={{ height: 15 }} />
              </>
            ))}
          </Image.PreviewGroup>
        </div>
      )}
    </Modal>
  );
};
