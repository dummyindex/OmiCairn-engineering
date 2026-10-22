import { Form, Input, Modal, message } from 'antd';
import { useModel } from 'umi';
import { requestDataCollect } from '@/request/data';

const CollectDataSourceForm = (props: any) => {
  const { form } = props;
  return (
    <Form
      form={form}
      labelAlign="right"
      labelCol={{ span: 4 }}
      wrapperCol={{ span: 20 }}
      autoComplete="off"
    >
      <Form.Item label="Save as:" key="name" required name="name">
        <Input />
      </Form.Item>
    </Form>
  );
};

const CollectDataSource = () => {
  const [dataSourceForm] = Form.useForm();
  const { dataCollectedNodeId, setDataCollectedNodeId } = useModel('analysis');

  const confirmCollectDataSource = async () => {
    const { name } = dataSourceForm.getFieldsValue();
    if (!name) {
      message.warning('name is required!');
      return;
    } else {
      const result = await requestDataCollect(dataCollectedNodeId, name);
      if (result.code === 200) {
        message.success('collect dataSource successful');
      }
      setDataCollectedNodeId(null);
    }
  };

  return (
    <Modal
      centered
      title="Save node data"
      open={dataCollectedNodeId}
      onOk={confirmCollectDataSource}
      onCancel={() => {
        setDataCollectedNodeId(null);
      }}
    >
      <CollectDataSourceForm form={dataSourceForm} />
    </Modal>
  );
};

export default CollectDataSource;
