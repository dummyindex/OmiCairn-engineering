import { useEffect } from 'react';
import { AnalysisType } from '@/constants/analysis';
import { Button, Modal, Form, Input, message } from 'antd';
import { useModel } from 'umi';

const UpdateNodeNameForm = (props: any) => {
  const { form } = props;

  return (
    <Form
      form={form}
      labelAlign="right"
      labelCol={{ span: 4 }}
      wrapperCol={{ span: 20 }}
      autoComplete="off"
    >
      <Form.Item label="name" key="name" required name="name">
        <Input />
      </Form.Item>
    </Form>
  );
};

const RenameNode = () => {
  const { dictionary } = useModel('localization');
  const { analysisAccessType, renamedNodeId, closeRenameNode, renamedNodeForm, renameNode, nodes } =
    useModel('analysis');

  const confirmEditNodeName = () => {
    const { name } = renamedNodeForm.getFieldsValue();
    if (!name) {
      message.warning('name is required!');
      return;
    }
    if (!renamedNodeId) {
      message.warning('renamed node id is required!');
      return;
    }
    renameNode(renamedNodeId, name);
    closeRenameNode();
  };

  const fillForm = () => {
    if (renamedNodeId) {
      const node = nodes.find((item: any) => item.id === renamedNodeId);
      if (!node) {
        return;
      }
      renamedNodeForm.setFieldsValue({ name: node.data.label });
    }
  };

  useEffect(() => {
    fillForm();
  }, [renamedNodeId]);

  return (
    <Modal
      centered
      title={dictionary.RENAME}
      open={!!renamedNodeId}
      onOk={(event: any) => {
        event.stopPropagation();
        confirmEditNodeName();
      }}
      onCancel={(e) => {
        e.stopPropagation();
        closeRenameNode();
      }}
      footer={[
        <Button
          key="back"
          onClick={() => {
            closeRenameNode();
          }}
        >
          {dictionary.CANCEL}
        </Button>,
        <Button
          key="submit"
          type="primary"
          disabled={analysisAccessType === AnalysisType.PUBLIC}
          onClick={() => {
            confirmEditNodeName();
          }}
        >
          {dictionary.CONFIRM}
        </Button>,
      ]}
    >
      <UpdateNodeNameForm form={renamedNodeForm} />
    </Modal>
  );
};

export default RenameNode;
