import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { UserOutlined } from '@ant-design/icons';
import { history, useModel } from 'umi';
import { Row, Col, Divider } from 'antd';
import MiniBell from '@/components/common/miniBell';

export default function ControlCenterHead() {
  const { userInfo, immediateRefresh, isGuest } = useModel('user');
  const { dictionary } = useModel('localization');
  const spacingXs = '0.5vh';
  const iconSize = '1.5vh';
  const textSize = '1.5vh';

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isGuest');
    immediateRefresh();
    history.push('/login/byPassword');
  };

  const isGuestUser = isGuest();

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
            <Col
              style={{
                cursor: 'pointer',
                fontSize: textSize,
                height: '3vh',
                display: 'flex',
                alignItems: 'center',
              }}
              onClick={logout}
            >
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
            </Col>
          </>
        ) : (
          <Col
            style={{
              cursor: 'pointer',
              fontSize: textSize,
              height: '3vh',
              display: 'flex',
              alignItems: 'center',
            }}
            onClick={() => history.push('/login/byPassword')}
          >
            {dictionary.LOG_IN}
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
