import ControlCenterHead from '@/components/special/controlCenter/head';
import { Layout } from 'antd';
import { Outlet } from 'umi';
import UserCenterSide from '@/components/special/controlCenter/UserCenter/side';

const { Header, Content, Sider } = Layout;

const headerStyle: React.CSSProperties = {
  color: '#fff',
  height: '5vh',
  paddingInline: 50,
  lineHeight: '5vh',
  backgroundColor: '#364578',
};

const contentStyle: React.CSSProperties = {
  // textAlign: 'center',
  minHeight: '120',
  color: '#000',
  height: '95vh',
  width: '84vw',
  backgroundColor: '#F3F3F2',
};

const leftSiderStyle: React.CSSProperties = {
  height: '95vh',
  width: '16vw',
  color: '#000',
  backgroundColor: '#FFFFFF',
  boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.04)',
};

const UserCenter = () => {
  return (
    <Layout>
      <Header style={headerStyle}>
        <ControlCenterHead />
      </Header>
      <Layout>
        <Sider width="16vw" style={leftSiderStyle}>
          <UserCenterSide />
        </Sider>
        <Content style={contentStyle}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default UserCenter;
