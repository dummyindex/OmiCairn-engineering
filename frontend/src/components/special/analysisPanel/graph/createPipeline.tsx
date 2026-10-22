import { requestGroupPipelineGet, requestPipelineCollect } from '@/request/pipeline';
import { AutoComplete, Form, Input, message, Modal } from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';

const { TextArea } = Input;

const CreatePipeLine = (props: any) => {
  const { isModalOpen, onCancel } = props;
  const [form] = Form.useForm();
  const { instance, currentSelectedNodes } = useModel('analysis');
  const { dictionary } = useModel('localization');
  const [groupList, setGroupList] = useState([]);

  const getGroupList = async () => {
    const result = await requestGroupPipelineGet();
    setGroupList(result.data);
  };
  useEffect(() => {
    getGroupList();
  }, []);

  const pipelineCollect = async () => {
    const value = await form.validateFields();
    const nodeIdList = currentSelectedNodes.map((node) => node.id);
    const edges = instance.toObject().edges;
    const edgeIdList: string[] = [];
    edges.map((item: any) => {
      if (nodeIdList.includes(item.source) && nodeIdList.includes(item.target)) {
        edgeIdList.push(item.id);
      }
    });
    const result = await requestPipelineCollect(
      value.name,
      value.groupName,
      value.description,
      nodeIdList,
      edgeIdList,
    );
    if (result.code) {
      message.success('Collection successful');
    }
    form.resetFields();
    onCancel();
  };

  return (
    <div
      onKeyDown={(e) => {
        e.stopPropagation();
      }}
      onKeyUp={(e: any) => {
        e.stopPropagation();
      }}
      onClick={(e: any) => {
        e.stopPropagation();
      }}
    >
      <Modal
        centered
        title="Pipeline Collect"
        open={isModalOpen}
        onOk={pipelineCollect}
        okText={dictionary.ADD}
        onCancel={onCancel}
        destroyOnClose
      >
        <Form form={form} initialValues={{ remember: true }} autoComplete="off">
          <Form.Item
            label="name"
            name="name"
            rules={[{ required: true, message: 'Please input name!' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="group"
            name="groupName"
            rules={[{ required: true, message: 'Please input group name!' }]}
          >
            <AutoComplete allowClear dataSource={groupList} />
          </Form.Item>
          <Form.Item label="description" name="description">
            <TextArea />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CreatePipeLine;
