import { requestLoginByPassword } from '@/request/userAuthorization';
import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { Button, Input, Space } from 'antd';
import { useState } from 'react';
import { history } from 'umi';
import styles from './login.less';
import RegisterMessage from './registerDialog';
import { useModel } from 'umi';

const LoginByUserName = () => {
  const { immediateRefresh } = useModel('user');

  const [passwordNumber, setPasswordNumber] = useState('');
  const [passwordState, setPasswordState] = useState(false);
  const [userNameState, setUserNameState] = useState(false);
  const [userNameResult, setUserNameResult] = useState('');
  const [passwordResult, setPasswordResult] = useState('');
  const [userNameRule, setUserNameRule] = useState('');
  const [passwordRule, setPasswordRule] = useState('');
  const [showedRegisterDialog, setShowRegisterDialog] = useState(false);

  const registerUserName = (userName: string) => {
    setUserNameResult(userName);
  };

  const registerPassword = (password: string) => {
    setPasswordResult(password);
  };

  const onUserNameChange = (e: any) => {
    if (e.target.value === '') {
      setUserNameState(true);
      setUserNameRule('User name cannot be empty');
      registerUserName(e.target.value);
    }
    if (e.target.value.length > 8) {
      setUserNameState(true);
      setUserNameRule('The username is too long');
      registerUserName(e.target.value);
    }
    if (e.target.value !== '') {
      setUserNameState(false);
      setUserNameRule('');
      registerUserName(e.target.value);
    }
  };

  const onPasswordChange = (e: any) => {
    if (e.target.value === '') {
      setPasswordState(true);
      setPasswordRule('Password cannot be empty');
      setPasswordNumber(e.target.value);
    }
    if (e.target.value !== '') {
      setPasswordState(false);
      setPasswordRule('');
      setPasswordNumber(e.target.value);
      registerPassword(e.target.value);
    }
  };

  const logIn = async () => {
    if (userNameResult !== '' && passwordResult !== '') {
      const result = await requestLoginByPassword(userNameResult, passwordResult);
      if (result.code === 200) {
        const token = result.data;
        localStorage.setItem('token', token);
        localStorage.setItem('hadToken', 'true');
        immediateRefresh();
        history.push('/management/homeMain');
      }
    }
    if (userNameResult === '') {
      setUserNameRule('User name cannot be empty');
      setUserNameState(true);
    }
    if (userNameResult.length > 8) {
      setUserNameState(true);
      setUserNameRule('The username is too long');
    }
    if (passwordNumber === '') {
      setPasswordState(true);
      setPasswordRule('Password cannot be empty');
    }
  };

  return (
    <div className={styles.inputBox}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input
          style={{
            borderRadius: '8px',
            overflow: 'hidden',
          }}
          size="large"
          prefix={<UserOutlined className="site-form-item-icon" />}
          placeholder="input the user name"
          status={userNameState ? 'error' : ''}
          onChange={onUserNameChange}
        />
        <div
          style={{
            height: '1.5vh',
            fontSize: 12,
            visibility: userNameState ? 'visible' : 'hidden',
            color: '#ff4d4f',
          }}
        >
          {userNameRule}
        </div>
        <Input.Password
          style={{
            borderRadius: '8px',
            overflow: 'hidden',
          }}
          size="large"
          prefix={<LockOutlined className="site-form-item-icon" />}
          placeholder="input password"
          status={passwordState ? 'error' : ''}
          onChange={onPasswordChange}
          autoComplete="new-password"
        />
        <div
          style={{
            height: '1.5vh',
            fontSize: 12,
            visibility: passwordState ? 'visible' : 'hidden',
            color: '#ff4d4f',
          }}
        >
          {passwordRule}
        </div>
        <div
          style={{
            marginBottom: '2.5vh',
            float: 'right',
          }}
        >
          <div
            style={{ color: '#1677FF', cursor: 'pointer' }}
            onClick={() => setShowRegisterDialog(true)}
          >
            Register
          </div>
          <RegisterMessage isOpen={showedRegisterDialog} setIsOpen={setShowRegisterDialog} />
        </div>
        <Button
          style={{ width: '100%', height: '6vh', fontSize: '20px' }}
          type="primary"
          onClick={logIn}
        >
          Log in
        </Button>
      </Space>
    </div>
  );
};
export default LoginByUserName;
