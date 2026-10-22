import styleConfig from '@/styleConfig';
import { ConfigProvider } from 'antd';
import { useEffect } from 'react';
import { Outlet, useLocation } from 'umi';
export default function Layout() {
  const location = useLocation();

  useEffect(() => {
    document.title = 'OmiCairn';
  }, [location]);
  return (
    <ConfigProvider theme={{ token: { colorPrimary: styleConfig.primaryColor } }}>
      <Outlet />
    </ConfigProvider>
  );
}
