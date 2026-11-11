import UploadDataDialog from '@/components/special/globalDialog/uploadData';
import AgentHistoryModal from './aiActionsMenu/agentHistoryModal';
import AutoGenieModal from './aiActionsMenu/autoGenieModal';
import BeautfierModal from './aiActionsMenu/beautfierModal';
import BugFixerModal from './aiActionsMenu/bugFixerModal';
import AutoGenieContextModal from './autoGenieContextModal';
import AutoGenieProgressModal from './autoGenieProgressModal';
import BugFixerHistoryModal from './bugFixerHistoryModal';
import CalculationLogModal from './calculationLogModal';
import CollectDataSource from './collectDataSource';
import CreateFunctionBlock from './createFunctionBlock';
import DataCaptureModal from './dataCaptureModal';
import ErrorDataModal from './errorDataModal';
import FunctionBlockDetailModal from './functionBlockDetailModal';
import ImportDataDialog from './importData';
import JobDetailModal from './jobDetailsModal';
import JobInfoModal from './jobInfoModal';
import NodeDetailModal from './nodeDetailModal';
import OutputsList from './outputsList';
import PlotOnlyPanel from './plotOnlyPanel';
import RenameNode from './renameNode';
import RetagNode from './retagNode';
import FunctionBlockSelectModal from './selectFbModal';
import CodeModal from './showCodeModal';
import SwitchFunctionBlockVersion from './switchFunctionBlockVersion';
import ThirdPartyDataSource from './thirdPartyDataSource';
import UpdateFunctionBlock from './updateFunctionBlock';
import VitessceDetail from './vitessceDetail';
import WorkflowHelperModal from './workflowHelperModal';

const Overlays = () => {
  return (
    <>
      <UploadDataDialog />
      <ImportDataDialog />
      <PlotOnlyPanel />
      <FunctionBlockDetailModal />
      <NodeDetailModal />
      <UpdateFunctionBlock />
      <SwitchFunctionBlockVersion />
      <CodeModal />
      <CreateFunctionBlock />
      <RenameNode />
      <RetagNode />
      <WorkflowHelperModal />
      <VitessceDetail />
      <CalculationLogModal />
      <JobInfoModal />
      <JobDetailModal />
      <CollectDataSource />
      <OutputsList />
      <BugFixerHistoryModal />
      <AutoGenieContextModal />
      <ThirdPartyDataSource />
      <DataCaptureModal />
      <ErrorDataModal />
      <FunctionBlockSelectModal />
      <AutoGenieModal />
      <AutoGenieProgressModal />
      <BugFixerModal />
      <AgentHistoryModal />
      <BeautfierModal />
    </>
  );
};

export default Overlays;
