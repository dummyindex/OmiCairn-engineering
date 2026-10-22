import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import React, { useEffect, useState } from 'react';
import { Outlet, history } from 'umi';
import { requestUserInfo } from '@/request/userAuthorization';
import UmapBackground from './umapBackground';
import { Version, VersionUpdatedTime } from '@/constants';
import './umapLogin.less';

const Login = () => {
  const [cellCount, setCellCount] = useState<number | null>(null);
  const handleIsTokenMethod = async () => {
    if (!localStorage.getItem('token')) {
      return;
    }
    const { data: userInfo } = await requestUserInfo();
    if (!userInfo) {
      history.push('/login/byPassword');
      return;
    }
    history.push('/management/homeMain');
  };

  useEffect(() => {
    handleIsTokenMethod();
  }, []);

  return (
    <div className="umap-login-container">
      <UmapBackground opacity={0.3} onCellCountChange={setCellCount} />

      <div className="umap-cell-info">
        {cellCount !== null && (
          <p>
            Visualizing <span className="umap-cell-count">{cellCount.toLocaleString()}</span>{' '}
            example cells
          </p>
        )}
        <p>Synthetic UMAP-style embedding (decorative)</p>
      </div>

      <div className="umap-login-content">
        <div className="umap-login-card">
          <div className="umap-logo">
            <div style={{ marginBottom: '16px' }}>
              <CustomImage name={customIconNames.WHITELOGO} style={{ height: '6vh' }} />
            </div>
            <p>Multi-Agent Computational Platform</p>
          </div>

          <Outlet />
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          bottom: '10px',
          margin: '0 auto',
          textAlign: 'center',
          color: 'rgba(255, 255, 255, 0.6)',
          fontSize: '12px',
          width: '100%',
          zIndex: 10,
        }}
      >
        <div style={{ position: 'absolute', left: '30px', bottom: '10px', fontSize: '12px' }}>
          {Version} ( {VersionUpdatedTime} )
        </div>
      </div>
    </div>
  );
};

export default Login;
