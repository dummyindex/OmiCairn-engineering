import { useEffect } from 'react';
import { Button, Modal, Form, Input, message } from 'antd';
import { useModel } from 'umi';
import { AnalysisType } from '@/constants/analysis';

const UpdateNodeTagForm = (props: any) => {
  const { form } = props;

  return (
    <Form
      form={form}
      labelAlign="right"
      labelCol={{ span: 4 }}
      wrapperCol={{ span: 20 }}
      autoComplete="off"
    >
      <Form.Item label="tag" key="tag" required name="tag">
        <Input />
      </Form.Item>
    </Form>
  );
};

const RetagNode = () => {
  const { dictionary } = useModel('localization');
  const { analysisAccessType, retagNodeForm, retagNodeId, retagNode, closeRetagNode, nodes } =
    useModel('analysis');

  const confirmEditNodeTag = () => {
    const { tag } = retagNodeForm.getFieldsValue();
    if (!tag) {
      message.warning('tag is required!');
      return;
    }
    if (!retagNodeId) {
      message.warning('retaged node id is required!');
      return;
    }
    retagNode(retagNodeId, tag);
    closeRetagNode();
  };

  const fillForm = () => {
    if (retagNodeId) {
      const node = nodes.find((item: any) => item.id === retagNodeId);
      if (!node) {
        return;
      }
      retagNodeForm.setFieldsValue({ tag: node.data.tag });
    }
  };

  useEffect(() => {
    if (retagNodeId) {
      fillForm();
    }
  }, [retagNodeId]);

  return (
    <Modal
      centered
      title={dictionary.UPDATE_TAG}
      open={!!retagNodeId}
      onOk={(event: any) => {
        event.stopPropagation();
        confirmEditNodeTag();
      }}
      onCancel={(e) => {
        e.stopPropagation();
        closeRetagNode();
      }}
      footer={[
        <Button
          key="back"
          onClick={() => {
            closeRetagNode();
          }}
        >
          {dictionary.CANCEL}
        </Button>,
        <Button
          key="submit"
          type="primary"
          disabled={analysisAccessType === AnalysisType.PUBLIC}
          onClick={() => {
            confirmEditNodeTag();
          }}
        >
          {dictionary.OK}
        </Button>,
      ]}
    >
      <UpdateNodeTagForm form={retagNodeForm} />
    </Modal>
  );
};

export default RetagNode;
