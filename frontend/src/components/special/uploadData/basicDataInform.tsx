import { Form, Input, Select } from 'antd';
import { useModel } from 'umi';
import { AnalysisType } from '@/constants/analysis';

const formItemLayout = {
  labelCol: { span: 24 }, // Make the label span the full row
  wrapperCol: { span: 24 }, // Make the input span the full row
};

const speciesOptions = [
  { value: 'Mus musculus (Mouse)' },
  { value: 'Homo sapiens (Human)' },
  { value: 'Other species' },
];

const BasicDataInfoForm = (props) => {
  const { dictionary } = useModel('localization');
  const { isGuest } = useModel('user');
  const { analysisAccessType } = useModel('analysis');
  const isGuestUser = isGuest();

  const { form, showName } = props;
  return (
    <div>
      <Form form={form} {...formItemLayout} autoComplete="off">
        {showName && (
          <Form.Item
            label={dictionary.NAME}
            name="name"
            rules={[{ required: true, message: 'name cannot be empty!' }]}
          >
            <Input disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC} />
          </Form.Item>
        )}
        <Form.Item
          label={dictionary.SPECIES}
          name="species"
          rules={[{ required: true, message: 'Species cannot be empty!' }]}
        >
          <Select
            disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC}
            options={speciesOptions}
          />
        </Form.Item>
        <Form.Item
          label={dictionary.DESCRIPTION}
          name="description"
          rules={[{ required: true, message: 'Description cannot be empty!' }]}
        >
          <Input.TextArea
            disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC}
            rows={4}
            style={{ resize: 'vertical', minHeight: '70px' }}
          />
        </Form.Item>
      </Form>
    </div>
  );
};

export default BasicDataInfoForm;
