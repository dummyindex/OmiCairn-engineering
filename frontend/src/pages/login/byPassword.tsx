import { requestLoginByPassword } from '@/request/userAuthorization';
import { EyeInvisibleOutlined, EyeOutlined, QuestionOutlined } from '@ant-design/icons';
import { Button, Input, Space, Tooltip } from 'antd';
import { useState } from 'react';
import { history, useModel } from 'umi';
import RegisterMessage from './registerDialog';

const LoginByPasswordBox = () => {
  const { immediateRefresh } = useModel('user');
  const { dictionary } = useModel('localization');
  const [account, setAccount] = useState('');
  const [accountState, setAccountState] = useState(false);
  const [passwordState, setPasswordState] = useState(false);
  const [accountRule, setAccountRule] = useState('');
  const [passwordRule, setPasswordRule] = useState('');
  const [passwordResult, setPasswordResult] = useState('');
  const [showedRegisterDialog, setShowRegisterDialog] = useState(false);
  const [areaCode, setAreaCode] = useState('');
  const [passwordVisible, setPasswordVisible] = useState(false);

  const handleGuestLogin = () => {
    localStorage.setItem('isGuest', 'true');
    const returnUrl = sessionStorage.getItem('returnUrl');
    if (returnUrl) {
      sessionStorage.removeItem('returnUrl');
      history.push(returnUrl);
    } else {
      history.push('/management/homeMain');
    }
  };

  const onAccountChange = (e: any) => {
    const accountValue = e.target.value;
    setAccount(accountValue);

    if (accountValue === '') {
      setAccountState(true);
      setAccountRule('Account cannot be empty');
    } else if (!/^\d+$/.test(accountValue)) {
      setAccountState(true);
      setAccountRule('Please enter a valid account format');
    } else {
      setAccountState(false);
      setAccountRule('');
    }
  };

  const selectChange = (value: string) => {
    setAreaCode(value);
  };

  const onPasswordChange = (e: any) => {
    const passwordValue = e.target.value;
    setPasswordResult(passwordValue);

    if (passwordValue === '') {
      setPasswordState(true);
      setPasswordRule('Password cannot be empty');
    } else {
      setPasswordState(false);
      setPasswordRule('');
    }
  };

  const logIn = async () => {
    if (passwordResult !== '' && account !== '' && !accountState) {
      const result = await requestLoginByPassword(areaCode + account, passwordResult);
      if (result.code === 200) {
        const token = result.data;
        localStorage.setItem('token', token);
        localStorage.setItem('hadToken', 'true');
        localStorage.removeItem('isGuest');
        immediateRefresh();
        history.push('/management/homeMain');
      }
    }
    if (account === '') {
      setAccountState(true);
      setAccountRule('Account cannot be empty');
    }
    if (passwordResult === '') {
      setPasswordState(true);
      setPasswordRule('Password cannot be empty');
    }
  };

  return (
    <div>
      <Space direction="vertical" style={{ width: '100%' }} size={0}>
        <div className="umap-form-group" style={{ marginBottom: '24px' }}>
          <label style={{ marginBottom: '12px' }}>Account number</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Input
              placeholder="+"
              className="umap-area-code"
              value={areaCode}
              onChange={(e) => selectChange(e.target.value.trim())}
              style={{
                width: '80px',
                height: '50px',
                backgroundColor: 'rgba(255,255,255,0.1)',
                border: '2px solid rgba(255,255,255,0.2)',
                borderRadius: '12px',
                color: 'white',
              }}
            />
            <Input
              size="large"
              placeholder="Enter your account number"
              value={account}
              status={accountState ? 'error' : ''}
              onChange={onAccountChange}
              style={{
                backgroundColor: 'rgba(255,255,255,0.1)',
                border: '2px solid rgba(255,255,255,0.2)',
                borderRadius: '12px',
                color: 'white',
                height: '50px',
                flex: 1,
              }}
            />
          </div>
          <div
            style={{
              height: '20px',
              fontSize: 12,
              visibility: accountState ? 'visible' : 'hidden',
              color: '#ff4d4f',
              marginTop: '6px',
            }}
          >
            {accountRule}
          </div>
        </div>

        <div className="umap-form-group" style={{ marginBottom: '40px' }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px', gap: '8px' }}>
            <label>Password</label>
            {passwordVisible ? (
              <EyeInvisibleOutlined
                onClick={() => setPasswordVisible(false)}
                style={{ cursor: 'pointer', color: 'rgba(255,255,255,0.6)' }}
              />
            ) : (
              <EyeOutlined
                onClick={() => setPasswordVisible(true)}
                style={{ cursor: 'pointer', color: 'rgba(255,255,255,0.6)' }}
              />
            )}
          </div>
          <Input
            size="large"
            type={passwordVisible ? 'text' : 'password'}
            placeholder="Enter your password"
            status={passwordState ? 'error' : ''}
            onChange={onPasswordChange}
            style={{
              backgroundColor: 'rgba(255,255,255,0.1)',
              border: '2px solid rgba(255,255,255,0.2)',
              borderRadius: '12px',
              color: 'white',
              height: '50px',
            }}
          />
          <div
            style={{
              height: '20px',
              fontSize: 12,
              visibility: passwordState ? 'visible' : 'hidden',
              color: '#ff4d4f',
              marginTop: '6px',
            }}
          >
            {passwordRule}
          </div>
        </div>

        <div style={{ marginBottom: '32px' }}>
          <Button
            className="umap-login-button"
            type="primary"
            size="large"
            onClick={logIn}
            style={{
              width: '100%',
              height: '50px',
              backgroundColor: '#3498db',
              borderColor: '#3498db',
              borderRadius: '12px',
              fontSize: '16px',
              fontWeight: '600',
            }}
          >
            {dictionary.LOG_IN}
          </Button>
        </div>

        <div className="umap-signup-link">
          <Space direction="horizontal" align="center" size={12}>
            <a
              onClick={handleGuestLogin}
              style={{ color: 'white', textDecoration: 'none', fontWeight: '600' }}
            >
              {dictionary.LOGIN_AS_A_GUEST}
            </a>
            <Tooltip title="Guest users can only use the system with limited permissions.">
              <QuestionOutlined style={{ cursor: 'pointer', color: 'rgba(255,255,255,0.6)' }} />
            </Tooltip>
          </Space>
        </div>

        <RegisterMessage isOpen={showedRegisterDialog} setIsOpen={setShowRegisterDialog} />
      </Space>
    </div>
  );
};

export default LoginByPasswordBox;
