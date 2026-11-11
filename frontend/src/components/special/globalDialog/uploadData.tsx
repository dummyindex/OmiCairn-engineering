import AnndataUpload from '@/components/special/uploadData/anndata';
import { UploadType } from '@/constants/data';
import { Alert, Layout, Menu, Modal, message } from 'antd';
import { useModel } from 'umi';
import AssembleUpload from '@/components/special/uploadData/assemble';
import FastqUpload from '@/components/special/uploadData/fastq';
import Outs from '@/components/special/uploadData/outs';
import SpaceRangerCount from '@/components/special/uploadData/spaceRangerCount';
import SeuratObjectRdsUpload from '@/components/special/uploadData/seuratObjectRds';
import GeneralUpload from '../uploadData/general';

interface ItemType {
  label: string;
  key: string;
  disabled?: boolean;
  style?: React.CSSProperties;
  title?: string;
}

interface MenuClickEvent {
  item: ItemType;
  key: string;
  keyPath: string[];
  domEvent: Event;
}

const UploadDataDialog = () => {
  const uploadDataUIModel = useModel('uploadDataUI');
  const { targetAnalysisId, showUploadDataUI, uploadType, setUploadType, closeUploadDataUI } =
    uploadDataUIModel;
  const { dictionary } = useModel('localization');
  const { analysisAccessType } = useModel('analysis');
  const { isGuest } = useModel('user');
  const items: ItemType[] = [
    {
      label: UploadType.ANNDATA,
      key: UploadType.ANNDATA,
    },
    {
      label: UploadType.OUTS,
      key: UploadType.OUTS,
    },
    {
      label: UploadType.ASSEMBLE,
      key: UploadType.ASSEMBLE,
    },
    // {
    //   label: UploadType.FASTQ,
    //   key: UploadType.FASTQ,
    // },
    {
      label: UploadType.SPACERANGER_COUNT,
      key: UploadType.SPACERANGER_COUNT,
    },
    {
      label: UploadType.SEURAT_OBJECT_RDS,
      key: UploadType.SEURAT_OBJECT_RDS,
    },
    {
      label: UploadType.GENERAL,
      key: UploadType.GENERAL,
    },
  ];

  const toggleUpdateType = (event: MenuClickEvent) => {
    const { key } = event;
    if (key === UploadType.FASTQ) {
      message.warning('FASTQ upload is not implemented in this release.');
      setUploadType(uploadType);
      return;
    }
    setUploadType(key);
  };

  const renderUploadPanel = () => {
    switch (uploadType) {
      case UploadType.ANNDATA:
        return (
          <AnndataUpload
            {...uploadDataUIModel}
            analysisAccessType={analysisAccessType}
            dictionary={dictionary}
            isGuest={isGuest}
          />
        );
      case UploadType.ASSEMBLE:
        return <AssembleUpload />;
      case UploadType.FASTQ:
        return <FastqUpload />;
      case UploadType.OUTS:
        return <Outs />;
      case UploadType.SPACERANGER_COUNT:
        return <SpaceRangerCount />;
      case UploadType.SEURAT_OBJECT_RDS:
        return <SeuratObjectRdsUpload />;
      case UploadType.GENERAL:
        return <GeneralUpload />;
      default:
        return null;
    }
  };

  return (
    <Modal
      centered
      destroyOnClose
      open={showUploadDataUI}
      onCancel={closeUploadDataUI}
      cancelText="close"
      title={dictionary.UPLOAD}
      okButtonProps={{ hidden: true }}
      cancelButtonProps={{ hidden: true }}
      width="min(90vw, 1200px)"
      style={{ minWidth: '320px' }}
    >
      <Layout
        style={{
          flexDirection: 'row',
          minHeight: '60vh',
          maxHeight: '80vh',
          height: '70vh',
        }}
      >
        <Layout.Sider
          theme="light"
          width="200px"
          style={{
            height: '100%',
            flex: '0 0 auto',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Menu
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
              flex: 1,
            }}
            selectedKeys={[uploadType]}
            onClick={toggleUpdateType}
            items={items}
            mode="vertical"
          />
        </Layout.Sider>
        <Layout.Content
          style={{
            padding: '16px',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {targetAnalysisId !== null && (
            <Alert
              style={{
                margin: '1rem 2rem 0 2rem',
              }}
              message={`In this mode, uploaded data will be imported in the current analysis automatically.`}
              type="info"
              showIcon
            />
          )}
          {renderUploadPanel()}
        </Layout.Content>
      </Layout>
    </Modal>
  );
};

export default UploadDataDialog;
