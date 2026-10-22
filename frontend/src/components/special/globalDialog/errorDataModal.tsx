import { useModel } from 'umi';

import { Modal, Button } from 'antd';

const ErrorDataModal = () => {
  const { closeErrorDataUI, showErrorDataUI, targetDataInfo } = useModel('errorData');
  const { dictionary } = useModel('localization');

  return (
    <Modal
      title={dictionary.ERROR_MESSAGE}
      visible={showErrorDataUI}
      onCancel={closeErrorDataUI}
      centered
      footer={[
        <Button key="back" onClick={closeErrorDataUI}>
          {dictionary.CLOSE}
        </Button>,
      ]}
    >
      <pre
        style={{
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          overflow: 'auto',
        }}
      >
        {targetDataInfo?.errorMessage}
      </pre>
    </Modal>
  );
};

export default ErrorDataModal;
