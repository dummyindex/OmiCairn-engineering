import { FolderOutlined, SettingOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useEffect } from 'react';
import DataCaptureToolDetails from './captureDataToolDetails';
import ChangeNodeToolDetails from './changeCurrentNodeToolDetails';
import CreateDataNodeToolDetails from './createDataNodeToolDetails';
import CreateReportToolDetails from './createReportToolDetails';
import GetAnalysisInfoToolDetails from './getAnalysisInfoToolDetails';
import GetAvailableFunctionBlocksToolDetails from './getAvailableFunctionBlocksToolDetails';
import GetComputationDetailsToolDetails from './getComputationDetailsToolDetails';
import GetFunctionBlockCodesToolDetails from './getFunctionBlockCodesToolDetails';
import OtherToolDetails from './otherToolDetails';
import PlanAutoGenieToolDetails from './planAutoGenieToolDetails';
import ProcessGeneralInputFolderToolDetails from './processGeneralInputFolderToolDetails';
import ProcessH5adFileToolDetails from './processH5adFileToolDetails';
import ReadFileToolDetails from './readFileToolDetails';
import RunAutoGenieToolDetails from './runAutoGenieToolDetails';

const ActionsResultArea = ({
  setShowTreeModal,
  setShowFileDrawer,
  subTaskList,
  chatInfo,
  focusedActionDetailsId,
}: any) => {
  const renderOperationContent = (subTask: any) => {
    switch (subTask.toolName) {
      case 'get_analysis_info':
        return <GetAnalysisInfoToolDetails subTask={subTask} />;
      case 'capture_data':
        return <DataCaptureToolDetails subTask={subTask} analysisId={chatInfo?.analysisId} />;
      case 'change_current_node':
        return <ChangeNodeToolDetails subTask={subTask} />;
      case 'plan_autogenie':
        return <PlanAutoGenieToolDetails subTask={subTask} />;
      case 'run_autogenie':
        return <RunAutoGenieToolDetails subTask={subTask} />;
      case 'create_data_node':
        return <CreateDataNodeToolDetails subTask={subTask} />;
      case 'get_function_block_codes':
        return <GetFunctionBlockCodesToolDetails subTask={subTask} />;
      case 'get_computation_details':
        return <GetComputationDetailsToolDetails subTask={subTask} />;
      case 'create_report':
        return <CreateReportToolDetails subTask={subTask} />;
      case 'get_available_function_blocks':
        return <GetAvailableFunctionBlocksToolDetails subTask={subTask} />;
      case 'read_file':
        return <ReadFileToolDetails subTask={subTask} />;
      case 'process_h5ad_file':
        return <ProcessH5adFileToolDetails subTask={subTask} />;
      case 'process_general_input_folder':
        return <ProcessGeneralInputFolderToolDetails subTask={subTask} />;
      default:
        return <OtherToolDetails subTask={subTask} />; // Detail component for other tools
    }
  };

  useEffect(() => {
    if (!focusedActionDetailsId) return;
    const element = document.getElementById(focusedActionDetailsId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [focusedActionDetailsId]);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '20px' }}>
      <div
        style={{
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h3 style={{ margin: 0, color: '#333' }}>Actions List</h3>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            icon={<FolderOutlined />}
            type="text"
            style={{ color: '#5974CE' }}
            onClick={() => setShowFileDrawer(true)}
          >
            View Files
          </Button>
          <Button
            icon={<SettingOutlined />}
            type="text"
            style={{ color: '#5974CE' }}
            onClick={() => setShowTreeModal(true)}
          >
            View Tree
          </Button>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {subTaskList &&
          subTaskList.length > 0 &&
          subTaskList.map((subTask: any) => {
            return (
              <div key={subTask.id} id={subTask.toolCallId}>
                {renderOperationContent(subTask)}
              </div>
            );
          })}
        {(!subTaskList || subTaskList.length === 0) && (
          <div
            style={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#999',
            }}
          >
            <div style={{ textAlign: 'center' }}>
              <SettingOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
              <div>The corresponding actions will be shown once a conversation starts</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActionsResultArea;
