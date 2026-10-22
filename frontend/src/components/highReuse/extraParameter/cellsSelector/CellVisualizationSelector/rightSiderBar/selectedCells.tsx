import { cellSelectorAdata } from '@/util/anndata';
import { cellSelectorFilter as cellFilter } from '@/util/cellFilter';
import { Col, Collapse, Checkbox, List, Row } from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';
const { Panel } = Collapse;

const SEGMENT = 30;

const SelectedCells = () => {
  const {
    dimensions,
    brushSelectedTable,
    cellFilterVersionUuid,
    selectedCellDict,
    setSelectedCellDict,
  } = useModel('cellSelect');

  const [selectedCells, setSelectedCells] = useState<string[]>([]);

  const [showedCount, setShowedCount] = useState<number>(SEGMENT);

  const [loading, setLoading] = useState<boolean>(false);

  const [scrollTimer, setScrollTimer] = useState<NodeJS.Timeout | null>(null);

  const [checkAll, setCheckAll] = useState(true);

  const onScroll = (e: any) => {
    if (scrollTimer) {
      clearTimeout(scrollTimer);
    }
    setScrollTimer(
      setTimeout(() => {
        const { scrollTop, scrollHeight, clientHeight } = e.target;
        if (scrollTop + clientHeight + 20 >= scrollHeight) {
          setShowedCount(showedCount + SEGMENT);
        }
      }, 200),
    );
  };
  const isMasked = (index: number) => {
    return (
      (brushSelectedTable && !brushSelectedTable?.at(index)) || !cellFilter?.queryByIndex(index)
    );
  };

  const computeSelectedCells = async () => {
    setLoading(true);
    try {
      const obsNames = await cellSelectorAdata.getObsNames();
      if (!obsNames) return;
      const selectedCells = obsNames.filter((obsName: string, index: number) => {
        return !isMasked(index);
      });
      setSelectedCells(selectedCells.getElements());
    } catch (err) {
      setSelectedCells([]);
      console.log(err);
    } finally {
      setLoading(false);
    }
  };

  const onSelect = (cell: string, checked: boolean) => {
    if (checked) {
      selectedCellDict[cell] = true;
      setSelectedCellDict({ ...selectedCellDict });
    } else {
      delete selectedCellDict[cell];
      setSelectedCellDict({ ...selectedCellDict });
    }
    setCheckAll(selectedCells.length === Object.keys(selectedCellDict).length);
  };

  useEffect(() => {
    computeSelectedCells();
  }, [brushSelectedTable, dimensions, cellFilterVersionUuid]);
  useEffect(() => {
    if (selectedCells && checkAll) {
      selectedCells.forEach((item) => {
        selectedCellDict[item] = true;
      });
      setSelectedCellDict({
        ...selectedCellDict,
      });
    }
  }, [selectedCells, checkAll]);

  const onCheckAllChange = (e: any) => {
    if (e.target.checked) {
      selectedCells.forEach((item) => {
        selectedCellDict[item] = true;
      });
      setSelectedCellDict({
        ...selectedCellDict,
      });
    }

    if (!e.target.checked) {
      setSelectedCellDict({});
    }

    setCheckAll(e.target.checked);
  };

  return (
    <>
      <Collapse
        style={{
          width: '100%',
          marginBottom: '1vh',
        }}
      >
        <Panel
          key="selectedCellsPanel"
          header={
            <Row>
              <Col>{`Selected Cells ( ${Object.keys(selectedCellDict).length} )`}</Col>
              <Col style={{ flex: 1 }} />
              <Col
                onClick={(e) => {
                  e.stopPropagation();
                }}
              >
                <Checkbox
                  onChange={(e) => {
                    e.stopPropagation();
                    onCheckAllChange(e);
                  }}
                  checked={checkAll}
                >
                  Check all
                </Checkbox>
              </Col>
            </Row>
          }
        >
          <div
            style={{
              width: '100%',
              height: '100%',
              maxHeight: '30vh',
              overflowY: 'auto',
            }}
            onScroll={onScroll}
          >
            <List loading={loading}>
              {selectedCells.slice(0, showedCount).map((cellName: string) => {
                return (
                  <Row key={cellName}>
                    <Checkbox
                      checked={selectedCellDict[cellName]}
                      style={{
                        margin: '10px 0',
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                      }}
                      onChange={(e) => {
                        onSelect(cellName, e.target.checked);
                      }}
                    >
                      <div
                        style={{
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {cellName}
                      </div>
                    </Checkbox>
                  </Row>
                );
              })}
            </List>
          </div>
        </Panel>
      </Collapse>
    </>
  );
};

export default SelectedCells;
