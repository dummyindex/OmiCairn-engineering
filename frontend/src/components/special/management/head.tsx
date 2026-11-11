import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { UserOutlined, LoginOutlined } from '@ant-design/icons';
import { useModel } from 'umi';
import { Menu, Dropdown, Row, Col, Divider } from 'antd';
import MiniBell from '@/components/common/miniBell';
import { history } from 'umi';

export default function ManagementHead() {
  const { userInfo, immediateRefresh, isGuest } = useModel('user');
  const { dictionary } = useModel('localization');

  const isGuestUser = isGuest();
  const spacingXs = '0.5vh';
  const iconSize = '1.5vh';
  const textSize = '1.5vh';

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isGuest');
    immediateRefresh();
    history.push('/login/byPassword');
  };

  const userMenu = (
    <Menu>
      <Menu.Item
        key="1"
        onClick={() => {
          history.push('/controlCenter/userCenter/nameSetting');
        }}
        style={{ height: '3vh', lineHeight: '3vh', fontSize: textSize }}
      >
        {dictionary.USER_CENTER}
      </Menu.Item>
      <Menu.Item
        key="2"
        onClick={() => {
          history.push('/controlCenter/messageCenter/serviceBulletin');
        }}
        style={{ height: '3vh', lineHeight: '3vh', fontSize: textSize }}
      >
        {dictionary.MESSAGE_CENTER}
      </Menu.Item>
    </Menu>
  );

  const guestMenu = (
    <Menu>
      <Menu.Item
        key="1"
        icon={<LoginOutlined style={{ fontSize: iconSize }} />}
        onClick={() => {
          history.push('/login/byPassword');
        }}
        style={{ height: '3vh', lineHeight: '3vh', fontSize: textSize }}
      >
        {dictionary.LOG_IN}
      </Menu.Item>
    </Menu>
  );

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        height: '5vh',
      }}
    >
      <div>
        <CustomImage
          name={customIconNames.WHITELOGO}
          style={{ height: '5vh', cursor: 'pointer', marginTop: '1vh' }}
          onClick={() => history.push('/management/homeMain')}
        />
      </div>

      <Row gutter={10} align="middle">
        {!isGuestUser ? (
          <>
            <Col style={{ cursor: 'pointer', fontSize: textSize }} onClick={logout}>
              {dictionary.LOG_OUT}
            </Col>
            <Col>
              <Divider
                type="vertical"
                style={{
                  backgroundColor: 'white',
                  height: '3vh',
                }}
              />
            </Col>
            <Col>
              <MiniBell />
            </Col>
            <Col>
              <Divider
                type="vertical"
                style={{
                  backgroundColor: 'white',
                  height: '3vh',
                }}
              />
            </Col>
            <Col>
              <Dropdown overlay={userMenu}>
                <div
                  style={{
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    height: '3vh',
                    fontSize: textSize,
                  }}
                >
                  <UserOutlined style={{ fontSize: iconSize, marginRight: spacingXs }} />
                  {userInfo?.userName || ''}
                </div>
              </Dropdown>
            </Col>
          </>
        ) : (
          <Col>
            <Dropdown overlay={guestMenu}>
              <div
                style={{
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  height: '3vh',
                  fontSize: textSize,
                }}
              >
                <UserOutlined style={{ fontSize: iconSize, marginRight: spacingXs }} />{' '}
                {dictionary.GUEST}
              </div>
            </Dropdown>
          </Col>
        )}
        <Col>
          <Divider
            type="vertical"
            style={{
              backgroundColor: 'white',
              height: '3vh',
            }}
          />
        </Col>
      </Row>
    </div>
  );
}
