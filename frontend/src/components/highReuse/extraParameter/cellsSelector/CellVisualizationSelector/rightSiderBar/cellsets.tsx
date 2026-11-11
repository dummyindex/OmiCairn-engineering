import { Checkbox, Col, Collapse, List, Row } from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';

const { Panel } = Collapse;

const SEGMENT = 30;

const Cellset = (props) => {
  const { cellsets, cellsetDict, setCellsetDictDict } = useModel('cellSelect');
  const { cellsetName } = props;
  const cellset = cellsets[cellsetName];

  const cellNameList = cellset.cells;
  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);
  // const [cellList, setCellList] = useState([] as any);
  const [showedCellList, setShowedCellList] = useState([] as any);

  const [showedCount, setShowedCount] = useState(50);

  const cellList = cellNameList.map((cell: string) => {
    return {
      name: cell.name,
      description: cell.description,
    };
  });

  const loadMoreData = () => {
    const moreList = [
      ...showedCellList,
      ...cellList.slice(showedCellList.length - 1, showedCellList.length - 1 + SEGMENT),
    ];
    setShowedCellList(moreList);
    setShowedCount(showedCount + SEGMENT);
  };

  const getShowedList = () => {
    return cellList.slice(0, showedCount);
  };

  const onManualSelect = (cell: string, checked: boolean) => {
    if (checked) {
      cellsetDict[cellsetName][cell] = true;
      setCellsetDictDict({ ...cellsetDict });
    } else {
      delete cellsetDict[cellsetName][cell];
      setCellsetDictDict({ ...cellsetDict });
    }
  };

  return (
    <div
      style={{
        width: '100%',
        height: '38vh',
        overflow: 'auto',
      }}
      onScroll={(e: any) => {
        const scrollTop = e.target.scrollTop;
        const childClientHeight = e.target.children[0].clientHeight;
        const clientHeight = e.target.clientHeight;
        if (scrollTop + clientHeight + 20 >= childClientHeight) {
          if (timer) {
            clearTimeout(timer);
          }
          setTimer(
            setTimeout(() => {
              loadMoreData();
            }, 500),
          );
        }
      }}
      onClick={(e) => {
        e.stopPropagation();
      }}
    >
      <List
        dataSource={getShowedList()}
        renderItem={(cell: any) => {
          return (
            <Checkbox
              checked={cellsetDict[cellsetName][cell.name]}
              style={{
                margin: '10px 0',
              }}
              onClick={(e) => {
                e.stopPropagation();
              }}
              onChange={(e) => {
                onManualSelect(cell.name, e.target.checked);
              }}
            >
              {cell.name}
            </Checkbox>
          );
        }}
      />
    </div>
  );
};

const Cellsets = () => {
  const { cellsets, cellsetDict, setCellsetDictDict } = useModel('cellSelect');
  const cellsetNames = Object.keys(cellsets);
  // const [checkAll, setCheckAll] = useState(true);
  useEffect(() => {
    const cellsetDict = {};
    Object.keys(cellsets).forEach((item) => {
      const cellDiect = {};
      cellsets[item].cells.map((element) => {
        return (cellDiect[element.name] = true);
      });
      cellsetDict[item] = cellDiect;
    });
    setCellsetDictDict({ ...cellsetDict });
  }, [cellsets]);

  const onCheckAllChange = (e: any, cellsetName: string) => {
    const newCheckAllState = e.target.checked;
    // setCheckAll(newCheckAllState);
    if (newCheckAllState) {
      const cellDiect = {};
      cellsets[cellsetName].cells.map((element) => {
        return (cellDiect[element.name] = true);
      });
      cellsetDict[cellsetName] = cellDiect;
      // Update the select-all state for the given cellsetName
      setCellsetDictDict({ ...cellsetDict });
    } else {
      // const cellDiect = {};
      // cellsets[cellsetName].cells.map((element) => {
      //   return (cellDiect[element.name] = false);
      // });
      // cellsetDict[cellsetName] = cellDiect;
      cellsetDict[cellsetName] = {};
      // Update the select-all state for the given cellsetName
      setCellsetDictDict({ ...cellsetDict });
    }
  };
  return (
    <>
      <Collapse>
        {cellsetNames.map((cellsetName: string) => {
          return (
            <Panel
              key={cellsetName}
              header={
                <Row>
                  <Col>{cellsetName}</Col>
                  <Col flex={1} />
                  <Col
                    onClick={(e) => {
                      e.stopPropagation();
                    }}
                  >
                    {' '}
                    <Checkbox
                      onClick={(e) => {
                        e.stopPropagation();
                      }}
                      onChange={(e) => {
                        onCheckAllChange(e, cellsetName);
                      }}
                      checked={
                        cellsetDict[cellsetName] &&
                        Object.keys(cellsetDict[cellsetName]).length ==
                          cellsets[cellsetName].cells.length
                      }
                    >
                      Check all
                    </Checkbox>
                  </Col>
                </Row>
              }
            >
              <Cellset cellsetName={cellsetName} />
            </Panel>
          );
        })}
      </Collapse>
    </>
  );
};

const CellsetsBar = () => {
  return (
    <>
      <Collapse
        collapsible="header"
        style={{
          width: '100%',
          marginBottom: '1vh',
        }}
      >
        <Panel key="cell set panel" header="cell sets">
          <Cellsets />
        </Panel>
      </Collapse>
    </>
  );
};
export default CellsetsBar;
