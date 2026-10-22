import { BreadComponent } from '@/components/common/breadComponent';
import { NodeType } from '@/constants/node';
import { loadGeneset, requestGetDataStructure } from '@/request/attachedData';
import { requestLatestComputation } from '@/request/computation';
import { FlowTool } from '@/util/flowTool';
import { SearchOutlined } from '@ant-design/icons';
import { Checkbox, Input, List, message, Modal, Select, Spin } from 'antd';
import React, { useEffect, useState } from 'react';
import { useModel } from 'umi';

const SEGMENT = 30;
const { Option } = Select;

const GenesSelectorModal = (props: any) => {
  const { isOpen, value, setIsOpen, onSubmit, nodeId } = props;
  const { instance } = useModel('analysis');
  const [genesets, setGenesets] = React.useState([] as any);
  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);
  const [selectedGeneDict, setSelectedGeneDict] = React.useState({} as any);
  const [checkAll, setCheckAll] = useState(false);
  const [selectedGenesetList, setSelectedGenesetList] = React.useState([] as any);

  const [maunalDict, setManualDict] = React.useState({} as any);

  const [geneList, setGeneList] = React.useState([] as any);
  const [showedGeneList, setShowedGeneList] = useState([] as any);

  const [searchKey, setSearchKey] = useState<string>('');

  const [showedCount, setShowedCount] = useState(50);
  const [loading, setLoading] = useState(false);

  const filteredGeneList = !searchKey
    ? geneList
    : geneList.filter((varName: string) =>
        varName.toUpperCase().includes(searchKey.trim().toUpperCase()),
      );

  const loadMoreData = () => {
    const moreList = [
      ...showedGeneList,
      ...geneList.slice(showedGeneList.length - 1, showedGeneList.length - 1 + SEGMENT),
    ];
    setShowedGeneList(moreList);
    setShowedCount(showedCount + SEGMENT);
  };

  const getShowedList = () => {
    if (searchKey) {
      return filteredGeneList.slice(0, showedCount);
    } else {
      return filteredGeneList.slice(0, showedCount);
    }
  };

  const closeGenesDialog = () => {
    // setSelectedGeneDict({});
    setIsOpen(false);
  };

  // const onToggleGeneset = (geneset: string, checked: boolean) => {
  const onToggleGeneset = (value) => {
    setSelectedGenesetList(value);
  };

  const onManualSelect = (gene: string, checked: boolean) => {
    const newManualDict = { ...maunalDict };
    if (checked) {
      newManualDict[gene] = true;
    } else {
      delete newManualDict[gene];
    }
    setManualDict(newManualDict);
  };

  const loadGeneList = async () => {
    setLoading(true);
    try {
      const flowTool = new FlowTool(instance);
      const result = flowTool.checkPreDataNode(nodeId);
      const node = flowTool.getNode(result);
      let dataId = '';
      if (node.type in [NodeType.DATA_NODE, NodeType.DATA_NODE_V2]) {
        dataId = node.data.dataId;
      } else if (node.type in [NodeType.COMPUTATION_NODE, NodeType.COMPUTATION_NODE_V2]) {
        const { data: latestComputation } = await requestLatestComputation(result);
        dataId = latestComputation.resultDataId;
      }

      const dataStructure = await requestGetDataStructure(dataId);
      const genesets = await loadGeneset(dataId);
      console.log('genesets', genesets);

      const varNames = dataStructure.var_names;
      const geneListCopy = [...varNames];
      setGenesets(genesets);
      setGeneList(geneListCopy.sort());
    } catch (e: any) {
      message.error(e.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (geneList) {
      setShowedGeneList(geneList.slice(0, SEGMENT));
    }
  }, [geneList]);

  const deletedSelected = (value: string) => {
    delete selectedGeneDict[value];
    delete maunalDict[value];
    setSelectedGeneDict({
      ...selectedGeneDict,
    });
    setManualDict({
      ...maunalDict,
    });
  };

  useEffect(() => {
    const newSelectedDict = {};
    for (const genesetName of selectedGenesetList) {
      const geneset = genesets[genesetName];

      const geneList = geneset.genes;
      for (const gene of geneList) {
        newSelectedDict[gene.name] = true;
      }
    }
    const manualGeneList = Object.keys(maunalDict);

    for (const gene of manualGeneList) {
      newSelectedDict[gene] = true;
    }
    setSelectedGeneDict(newSelectedDict);
  }, [selectedGenesetList, maunalDict]);

  useEffect(() => {
    if (isOpen) {
      const newSelectedGeneDict = {};
      if (value) {
        value.forEach((item: string) => {
          newSelectedGeneDict[item] = true;
        });
        setSelectedGeneDict(newSelectedGeneDict);
        setManualDict(newSelectedGeneDict);
      }
    }
  }, [isOpen, genesets]);

  useEffect(() => {
    if (isOpen) {
      loadGeneList();
    }
  }, [isOpen]);

  const onCheckAllChange = (e: any) => {
    if (e.target.checked) {
      filteredGeneList.map((item) => {
        selectedGeneDict[item] = true;
        setSelectedGeneDict({
          ...selectedGeneDict,
        });
      });
    }

    if (!e.target.checked) {
      const newSelectedDict = {};
      for (const genesetName of selectedGenesetList) {
        const geneset = genesets[genesetName];
        const geneList = Object.keys(geneset.genes);
        for (const gene of geneList) {
          newSelectedDict[gene] = true;
        }
      }
      const manualGeneList = Object.keys(maunalDict);

      for (const gene of manualGeneList) {
        newSelectedDict[gene] = true;
      }
      setSelectedGeneDict({ ...newSelectedDict });
    }
    setCheckAll(e.target.checked);
  };

  return (
    <Modal
      style={{ zIndex: '999' }}
      title="Select genes"
      onCancel={closeGenesDialog}
      open={isOpen}
      onOk={() => {
        onSubmit(Object.keys(selectedGeneDict));
        closeGenesDialog();
      }}
    >
      <Select
        mode="multiple"
        style={{ width: '100%' }}
        optionLabelProp="label"
        placeholder="select one geneset"
        onChange={onToggleGeneset}
      >
        {genesets &&
          Object.keys(genesets).map((geneset: string) => {
            return (
              <Option key={geneset} value={geneset} lable={geneset}>
                {geneset}
              </Option>
            );
          })}
      </Select>
      <div
        onClick={(e) => {
          e.stopPropagation();
        }}
        style={{ marginTop: '10px' }}
      >
        <BreadComponent
          boxWidth={8}
          selectedList={selectedGeneDict}
          deletedSelected={deletedSelected}
        />
        <div
          style={{
            width: '100%',
            marginBottom: '1vh',
            marginTop: '1vh',
          }}
        >
          <Input
            placeholder="input the gene name"
            allowClear
            size="middle"
            onClick={(e) => {
              e.stopPropagation();
            }}
            onChange={({ target: { value } }) => {
              setSearchKey(value);
            }}
            suffix={<SearchOutlined />}
          />
        </div>
        <div
          style={{
            backgroundColor: '#f1f3f4',
            borderRadius: '5px',
          }}
        >
          {loading ? (
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '38vh',
              }}
            >
              <Spin />
            </div>
          ) : (
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
              <Checkbox onChange={onCheckAllChange} checked={checkAll}>
                Check all
              </Checkbox>
              <List
                split={false}
                bordered={false}
                size="small"
                dataSource={getShowedList()}
                renderItem={(item: any) => {
                  return (
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'row',
                        alignItems: 'center',
                        justifyContent: 'flex-start',
                        marginLeft: '1vw',
                      }}
                    >
                      <Checkbox
                        checked={selectedGeneDict[item]}
                        style={{
                          margin: '10px 0',
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                        }}
                        onChange={(e) => {
                          onManualSelect(item, e.target.checked);
                        }}
                      >
                        <div
                          style={{
                            height: 30,
                          }}
                        >
                          {item}
                        </div>
                      </Checkbox>
                    </div>
                  );
                }}
              />
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};

GenesSelectorModal.defaultProps = {
  isOpen: false,
};

export default GenesSelectorModal;
