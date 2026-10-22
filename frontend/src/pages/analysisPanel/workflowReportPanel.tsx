import { Layout } from 'antd';
import WorkflowReportPage from '@/components/special/analysisPanel/workflowReport';

const { Content } = Layout;

export default function WorkflowReportPanel() {
  return (
    <Content
      style={{
        height: '95vh',
      }}
    >
      <WorkflowReportPage />
    </Content>
  );
}
