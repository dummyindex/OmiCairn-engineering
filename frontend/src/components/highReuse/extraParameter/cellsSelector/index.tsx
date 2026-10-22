import LeftSiderBar from './CellVisualizationSelector/leftSiderBar';
// import MiddleBox from './CellVisualizationSelector/middleBox/index';
import MiddleBox from './CellVisualizationSelector/middleBox';
import RightSider from './CellVisualizationSelector/rightSider';
import { Empty, Modal, Result, Spin } from 'antd';

import { useModel } from 'umi';

const CellVisualizationSelector = (props) => {
  const {
    error,
    loading,
    open,
    setOpen,
    selectedCellDict,
    cellsetDict,
    // setSelectedCellDict,
    setXyzDimensions,
    dataStructure,
  } = useModel('cellSelect');
  const { onSubmit } = props;

  const closeCellsDialog = () => {
    setOpen(false);
    setXyzDimensions([null, null, null]);
  };
  // const [selectedList, setSelectedList] = useState<string[]>([]);

  const renderModalBody = () => {
    if (loading) {
      return (
        <Spin size="large" tip="Cell Selector Loading...">
          <div
            style={{
              display: 'flex',
              // height: 75vh;
              justifyContent: 'space-between',
            }}
          >
            <div style={{ width: '17.5vw', height: '70vh' }} />
            <div style={{ width: '42vw', height: '70vh' }} />
            <div style={{ width: '20vw', height: '70vh' }} />
          </div>
        </Spin>
      );
    }
    if (error) {
      return (
        <Result
          status="error"
          title="Panel Loaded Failed"
          subTitle="Please refresh the page and try again."
        />
      );
    }
    if (!dataStructure) {
      return (
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Empty
            description="No Data Structure"
            imageStyle={{
              height: '15vh',
            }}
          />
        </div>
      );
    }
    return (
      <div
        style={{
          display: 'flex',
          // height: 75vh;
          justifyContent: 'space-between',
        }}
      >
        <div style={{ width: '17.5vw', height: '70vh' }}>
          <LeftSiderBar dataStructure={dataStructure} />
        </div>
        <div style={{ width: '42vw', height: '70vh' }}>
          <MiddleBox />
        </div>
        <div style={{ width: '20vw', height: '70vh' }}>
          <RightSider />
        </div>
      </div>
    );
  };

  return (
    <div>
      <Modal
        width="85vw"
        // height=" 55vh"
        destroyOnClose
        title="Select cells"
        onCancel={closeCellsDialog}
        okText="Select"
        open={open}
        onOk={() => {
          const cellList: string[] = [];

          for (const outerKey in cellsetDict) {
            const innerObject = cellsetDict[outerKey];
            for (const innerKey in innerObject) {
              cellList.push(innerKey);
            }
          }
          const keysArray = cellList.concat(Object.keys(selectedCellDict));
          // Deduplicate with a Set
          const uniqueKeysSet = new Set(keysArray);
          // Convert the Set to an array
          const uniqueKeysArray = [...uniqueKeysSet];

          onSubmit(uniqueKeysArray);
          closeCellsDialog();
          // setSelectedList(uniqueKeysArray);
        }}
        centered
      >
        {renderModalBody()}
      </Modal>
    </div>
  );
};

export default CellVisualizationSelector;
