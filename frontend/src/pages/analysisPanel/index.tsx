import PanelHead from '@/components/special/analysisPanel/head/panelHead';
import { Outlet } from 'umi';
import { Layout } from 'antd';
import { ReactFlowProvider } from 'reactflow';
import { useModel, useLocation } from 'umi';
import { useEffect } from 'react';
import { getLocationParams } from '@/util/getUrl';
const { Header } = Layout;
import { FigureCacheProvider } from '@/contexts/FigureCache';

const headerStyle: React.CSSProperties = {
  height: 'calc(5vh - 1px)',
  padding: '0 1.5vw',
  lineHeight: '5vh',
  backgroundColor: 'white',
  borderBottom: '0.5px solid rgb(151,151,151,0.2)',
};

export default function AnalysisPanel() {
  const location = useLocation();
  const { setAnalysisId } = useModel('analysis');

  useEffect(() => {
    const [analysisId] = getLocationParams(['analysis-id']);
    if (analysisId) {
      setAnalysisId(analysisId);
    }
    return () => {
      setAnalysisId('');
    };
  }, [location]);

  return (
    <FigureCacheProvider>
      <ReactFlowProvider>
        <Layout>
          <Header style={headerStyle}>
            <PanelHead />
          </Header>
          <Outlet />
        </Layout>
      </ReactFlowProvider>
    </FigureCacheProvider>
  );
}
