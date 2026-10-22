import Overlays from '@/components/special/globalDialog/overlays';
import ManagementHead from '@/components/special/management/head';
import HomeSider from '@/components/special/management/homeSider';
import { Layout } from 'antd';
import { Outlet } from 'umi';

const { Header } = Layout;

const headerStyle: React.CSSProperties = {
  color: '#fff',
  height: '5vh',
  paddingInline: 50,
  lineHeight: '5vh',
  backgroundColor: '#364578',
};

const Home = () => {
  return (
    <Layout>
      <Header style={headerStyle}>
        <ManagementHead />
      </Header>
      <div
        style={{
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'stretch',
          height: '95vh',
        }}
      >
        <div
          style={{
            width: 'auto',
            backgroundColor: '#FFFFFF',
            boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.04)',
          }}
        >
          <HomeSider />
        </div>
        <div
          style={{
            flex: 1,
            backgroundColor: '#F3F3F2',
          }}
        >
          <Outlet />
        </div>
      </div>
      <Overlays />
    </Layout>
  );
};

export default Home;
