import { DimensionSourceType } from '@/constants/cellSelector';
import { DownOutlined, SearchOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';
import {
  Button,
  Cascader,
  Checkbox,
  Dropdown,
  Form,
  Input,
  List,
  Menu,
  Modal,
  Space,
  Tooltip,
} from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';
import styles from './dimensionSwitch.less';

const SEGMENT = 50;

const GeneSelectedModal = (props) => {
  const { geneListToShow, getSelectedGene } = props;
  const [geneList, setGeneList] = useState(geneListToShow);
  const [showedGeneList, setShowedGeneList] = useState<any[]>([]);
  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);
  const [selectedGene, setSelectedGene] = useState(null);
  const [searchKey, setSearchKey] = useState<string>('');
  const [showedCount, setShowedCount] = useState(SEGMENT);
  // console.log('geneList', geneList);

  useEffect(() => {
    setGeneList(geneListToShow);
  }, []);

  useEffect(() => {
    if (geneList) {
      setShowedGeneList(geneList.slice(0, SEGMENT));
    }
  }, [geneList]);

  const filteredGeneList = !searchKey
    ? geneList
    : geneList.filter((varName: string) =>
        varName.toUpperCase().includes(searchKey.trim().toUpperCase()),
      );

  const loadMoreData = () => {
    const moreList = showedGeneList.concat(
      geneList.slice(showedGeneList.length - 1, showedGeneList.length - 1 + SEGMENT),
    );
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

  const handleCheckboxChange = (item) => {
    if (selectedGene === item) {
      // If the clicked item is already selected, deselect it
      setSelectedGene(null);
      getSelectedGene(null); // Notify the parent component of deselection
    } else {
      // Otherwise select the new item
      setSelectedGene(item);
      getSelectedGene(item); // Notify the parent component of the new selection
    }
  };

  return (
    <div>
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
            split={false}
            bordered={false}
            size="small"
            dataSource={getShowedList()}
            renderItem={(item) => {
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
                    style={{
                      margin: '10px 0',
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCheckboxChange(item);
                    }}
                    checked={selectedGene === item} // Controls whether it is checked
                    onChange={(e) => {
                      e.stopPropagation();
                      // selectedChange(item);
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
      </div>
    </div>
  );
};

const DimensionSwitch = () => {
  const [form] = Form.useForm();

  const { dataStructure, dimensions, updateEmbeddingDimensions }: any = useModel('cellSelect');
  const { setDimensionsLoading } = useModel('cellSelect');
  const [selectedGeneModal, setSelectedGeneModal] = useState(false);
  const [selectedGene, setSelectedGene] = useState('');
  const [selectedFormItem, setSelectedFormItem] = useState('');

  const [dialogOpen, setDialogOpen] = useState(false);

  const [dimensionOptions, setDimensionOptions] = useState<any[]>([]);
  const [zAxisShow, setZAxisShow] = useState(false);

  const { setXyzDimensions } = useModel('cellSelect');

  const obsm: any = dataStructure?.obsm || {};

  const obsmKeys = Object.keys(obsm).filter((key: string) => {
    return key.startsWith('X_');
  });

  const items: MenuProps['items'] = obsmKeys.map((key: string) => {
    const handledKey = key.replace('X_', '');
    return {
      key,
      label: handledKey,
    };
  });

  const openDialog = () => {
    setDialogOpen(true);
  };

  const closeDialog = () => {
    setDialogOpen(false);
  };

  const getSelectedGene = (gene) => {
    setSelectedGene(gene);
  };
  const submit = (values: any) => {
    setDimensionsLoading(true);
    const { x, y, z } = values;
    const [xDim, yDim, zDim] = [x, y, z].map((itemStr: string[]) => {
      if (!itemStr || itemStr.length == 0) return null;
      if (itemStr[0] === 'basis') {
        return {
          dimSource: DimensionSourceType.OBSM,
          dim: itemStr[2],
        };
      } else if (itemStr[0] === 'obs') {
        return {
          dimSource: DimensionSourceType.OBS,
          dim: itemStr[1],
        };
      } else if (itemStr[0] === 'genes') {
        return {
          dimSource: DimensionSourceType.X_COL,
          dim: itemStr[1],
        };
      }
    });

    updateEmbeddingDimensions([xDim, yDim, zDim]);
    setXyzDimensions([null, null, null]);
    setTimeout(() => {
      setDimensionsLoading(false);
    }, 1000);
    closeDialog();
  };

  // Grouping function
  function categorizeData(data) {
    const categorizedData = {};

    data.forEach((item) => {
      const parts = item.label.split('_'); // Split the label string
      if (parts.length > 2) {
        const middleWord = parts[1];
        if (!categorizedData[middleWord]) {
          categorizedData[middleWord] = [];
        }
        categorizedData[middleWord].push(item);
      }
    });

    return categorizedData;
  }

  useEffect(() => {
    if (!dataStructure) {
      setDimensionOptions([]);
      return;
    }

    const newDimensionOptions: any[] = [];
    // obsm
    const obsmDimensionOptions: any[] = [];
    const embeddingKeyList = Object.keys(dataStructure?.obsm || {}).filter(
      (embeddingKey: string) => {
        return embeddingKey.startsWith('X_');
      },
    );

    embeddingKeyList.forEach((embeddingKey: string) => {
      const embeddingShape = dataStructure?.obsm[embeddingKey] || [0, 0];
      obsmDimensionOptions.push(
        ...new Array(embeddingShape[1]).fill(0).map((_, index) => {
          const dimKey = `${embeddingKey}_${index}`;
          return {
            label: dimKey,
            value: `${dimKey}`,
            key: dimKey,
          };
        }),
      );
    });
    const result = categorizeData(obsmDimensionOptions);
    const obsmResult = Object.keys(result).map((item) => {
      return {
        label: item.toUpperCase(),
        value: `${item}`,
        children: result[item],
      };
    });
    newDimensionOptions.push({
      label: 'basis',
      value: 'basis',
      children: obsmResult,
    });

    // obs continuous col
    const obs = dataStructure?.obs || [];
    const obsContinuousOptions = obs
      .filter((obsItem: any) => {
        return obsItem.dtype.startsWith('float');
      })
      .map((obsItem: any) => {
        return {
          label: obsItem.key,
          value: `${obsItem.key}`,
          key: obsItem.key,
        };
      });

    newDimensionOptions.push({
      label: 'obs',
      value: 'obs',
      children: obsContinuousOptions,
    });

    // const genesResult = dataStructure.var_names;

    // const getShowedGeneList = genesResult.map((item) => {
    //   return {
    //     label: item,
    //     value: `${item}`,
    //     key: item,
    //   };
    // });

    newDimensionOptions.push({
      label: 'genes',
      value: 'genes',
      // children: [{ label: 'gene modal' }],
    });

    // // gene x col
    // const geneXOptions =
    setDimensionOptions(newDimensionOptions);
  }, [dataStructure]);

  useEffect(() => {
    if (dimensions) {
      const newInitialValues = {};

      const [xDim, yDim, zDim] = dimensions;
      if (!!xDim) {
        const { dimSource, dim } = xDim;
        let group = dimSource;
        if (dimSource === DimensionSourceType.OBSM) {
          group = 'basis';
          const dimArr = dim.split('_');
          newInitialValues.x = [group, dimArr[1].toUpperCase(), dim];
        } else if (dimSource === DimensionSourceType.X_COL) {
          group = 'genes';
          newInitialValues.x = [group, dim];
        } else {
          newInitialValues.x = [group, dim];
        }
      }
      if (!!yDim) {
        const { dimSource, dim } = yDim;
        let group = dimSource;
        if (dimSource === DimensionSourceType.OBSM) {
          group = 'basis';
          const dimArr = dim.split('_');
          newInitialValues.y = [group, dimArr[1].toUpperCase(), dim];
        } else if (dimSource === DimensionSourceType.X_COL) {
          group = 'genes';
          newInitialValues.y = [group, dim];
        } else {
          newInitialValues.y = [group, dim];
        }
      }
      if (!!zDim) {
        const { dimSource, dim } = zDim;
        let group = dimSource;
        if (dimSource === DimensionSourceType.OBSM) {
          group = 'basis';
          const dimArr = dim.split('_');
          newInitialValues.z = [group, dimArr[1].toUpperCase(), dim];
        } else if (dimSource === DimensionSourceType.X_COL) {
          group = 'genes';
          newInitialValues.z = [group, dim];
        } else {
          newInitialValues.z = [group, dim];
        }
      }

      form.setFieldsValue(newInitialValues);
    }
  }, [dimensions]);

  return (
    <div className={styles.dimensionSwitchContainer}>
      <Dropdown
        overlay={
          <Menu>
            <Menu.Item onClick={openDialog} style={{ background: '#eff1fc', color: '#606cb7' }}>
              Select dimensions
            </Menu.Item>
            {items &&
              items.map((item) => (
                <Menu.Item
                  key={item.key}
                  onClick={() => {
                    // updateEmbedding(item.key);
                    if (dataStructure?.obsm[item.key][1] < 3) {
                      updateEmbeddingDimensions([
                        { dimSource: DimensionSourceType.OBSM, dim: `${item.key}_0` },
                        { dimSource: DimensionSourceType.OBSM, dim: `${item.key}_1` },
                        { dimSource: DimensionSourceType.OBSM, dim: `${item.key}_umap` },
                      ]);
                      setZAxisShow(true);
                    } else {
                      updateEmbeddingDimensions([
                        { dimSource: DimensionSourceType.OBSM, dim: `${item.key}_0` },
                        { dimSource: DimensionSourceType.OBSM, dim: `${item.key}_1` },
                        { dimSource: DimensionSourceType.OBSM, dim: `${item.key}_2` },
                      ]);
                      setZAxisShow(false);
                    }
                  }}
                >
                  {item.label}
                </Menu.Item>
              ))}
          </Menu>
        }
        placement="bottomRight"
        trigger={['click']}
        arrow={{ pointAtCenter: true }}
      >
        <Tooltip title="change the showed dimensions">
          <Button>
            <Space>
              basis
              <DownOutlined />
            </Space>
          </Button>
        </Tooltip>
      </Dropdown>
      <Modal
        okText="Submit"
        open={dialogOpen}
        onCancel={closeDialog}
        onOk={() => {
          form.submit();
        }}
        className={styles.dialog}
        centered
      >
        <div className={styles.dialogTitle}>Select the dimensions:</div>
        <Form form={form} onFinish={submit} autoComplete="off">
          <Form.Item
            name="x"
            label="x"
            rules={[{ required: true, message: 'Please select the x coordinate!' }]}
          >
            <Cascader
              allowClear
              // loadData={loadMoreGeneData}
              options={dimensionOptions}
              showSearch
              suffixIcon={<SearchOutlined />}
              onChange={(value) => {
                if (value[0] == 'genes') {
                  setSelectedGeneModal(true);
                  setSelectedFormItem('x');
                }
              }}
            />
          </Form.Item>
          <Form.Item
            name="y"
            label="y"
            rules={[{ required: true, message: 'Please select the y coordinate!' }]}
          >
            <Cascader
              allowClear
              options={dimensionOptions}
              showSearch
              suffixIcon={<SearchOutlined />}
              onChange={(value) => {
                if (value[0] == 'genes') {
                  setSelectedGeneModal(true);
                  setSelectedFormItem('y');
                }
              }}
            />
          </Form.Item>
          <Form.Item
            name="z"
            label="z"
            rules={[{ required: true, message: 'Please select the z coordinate!' }]}
          >
            <Cascader
              allowClear
              options={dimensionOptions}
              disabled={zAxisShow}
              suffixIcon={<SearchOutlined />}
              showSearch
              onChange={(value) => {
                if (value[0] == 'genes') {
                  setSelectedGeneModal(true);
                  setSelectedFormItem('z');
                }
              }}
            />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        centered
        title="select a gene"
        open={selectedGeneModal}
        onOk={() => {
          form.setFieldsValue({
            [selectedFormItem]: ['genes', `${selectedGene}`], // Update the field value
          });
          setSelectedGeneModal(false);
          setSelectedFormItem('');
          setSelectedGene('');
        }}
        onCancel={() => {
          form.setFieldsValue({
            [selectedFormItem]: [], // Update the field value
          });
          setSelectedGeneModal(false);
        }}
        destroyOnClose
      >
        <GeneSelectedModal
          geneListToShow={dataStructure !== null ? dataStructure.var_names : []}
          getSelectedGene={getSelectedGene}
        />
      </Modal>
    </div>
  );
};

export default DimensionSwitch;
