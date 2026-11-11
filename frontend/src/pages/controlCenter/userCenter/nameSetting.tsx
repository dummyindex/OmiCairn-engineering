import { Form, Input, Button, message, Select } from 'antd';
import { useModel } from 'umi';
import style from '../index.less';
import { useEffect } from 'react';
import { requestEditUser } from '@/request/user';

const NameSetting = () => {
  const { userInfo, immediateRefresh } = useModel('user');
  const { dictionary } = useModel('localization');
  const [form] = Form.useForm();

  const onFinish = async (values: any) => {
    const { userName, email, phoneNumber, accountType } = values;
    try {
      await requestEditUser(
        userName,
        email,
        phoneNumber,
        accountType || userInfo?.accountType || '',
      );
      immediateRefresh();
      message.success('Edit user successfully');
    } catch {
      message.error('Failed to edit user');
    }
  };

  const onFinishFailed = (errorInfo) => {
    console.log('Failed:', errorInfo);
  };

  useEffect(() => {
    if (!userInfo) return;
    form.setFieldsValue({
      userName: userInfo.userName,
      email: userInfo.email,
      phoneNumber: userInfo.phoneNumber,
      accountType: userInfo.accountType || '',
    });
  }, [userInfo]);

  return (
    <div className={style.box}>
      <div className={style.card}>
        <div className={style.title}>{dictionary.INFORMATION_SETTING}</div>
        <div className={style.content} style={{ width: '60%' }}>
          <Form
            name="basic"
            form={form}
            labelCol={{ span: 4 }}
            wrapperCol={{ span: 12 }}
            onFinish={onFinish}
            onFinishFailed={onFinishFailed}
            autoComplete="off"
          >
            <Form.Item
              label={dictionary.USERNAME}
              name="userName"
              rules={[{ required: true, message: 'Please enter your username' }]}
            >
              <Input />
            </Form.Item>

            <Form.Item
              label={dictionary.EMAIL}
              name="email"
              rules={[{ required: true, message: 'Please enter your email' }]}
            >
              <Input type="email" />
            </Form.Item>

            <Form.Item
              label={dictionary.PHONE}
              name="phoneNumber"
              rules={[{ required: true, message: 'Please enter your phone' }]}
            >
              <Input type="tel" readOnly />
            </Form.Item>

            {userInfo?.accountType !== 'administrator' && (
              <Form.Item
                label={'Account Type'}
                name="accountType"
                rules={[{ required: true, message: 'Please select account type' }]}
              >
                <Select placeholder="Select account type">
                  <Select.Option value="personal">Personal</Select.Option>
                  <Select.Option value="enterprise">Enterprise</Select.Option>
                </Select>
              </Form.Item>
            )}

            <Form.Item wrapperCol={{ offset: 4, span: 16 }} style={{ marginTop: '2vw' }}>
              <Button type="primary" htmlType="submit">
                {dictionary.SUBMIT}
              </Button>
            </Form.Item>
          </Form>
        </div>
      </div>
    </div>
  );
};

export default NameSetting;
