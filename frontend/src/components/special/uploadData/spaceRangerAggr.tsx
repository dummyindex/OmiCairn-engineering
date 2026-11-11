// outs
// ├── aggregation.csv
// ├── aggr_tissue_positions.csv
// ├── analysis
// │   ├── clustering
// │   ├── diffexp
// │   ├── pca
// │   ├── tsne
// │   └── umap
// ├── cloupe.cloupe
// ├── filtered_feature_bc_matrix
// │   ├── barcodes.tsv.gz
// │   ├── features.tsv.gz
// │   └── matrix.mtx.gz
// ├── filtered_feature_bc_matrix.h5
// ├── spatial
// │   ├── LV123
// │   │   ├── scalefactors_json.json
// │   │   ├── tissue_hires_image.png
// │   │   └── tissue_lowres_image.png
// │   ├── LB456
// │   │   ├── scalefactors_json.json
// │   │   ├── tissue_hires_image.png
// │   │   └── tissue_lowres_image.png
// │   └── LP789
// │       ├── scalefactors_json.json
// │       ├── tissue_hires_image.png
// │       └── tissue_lowres_image.png
// ├── summary.json
// └── web_summary.html

import { useState, useEffect } from 'react';
import BasicDataInfoForm from './basicDataInform';
import { Form, Button, Row, Col, Tree, message, Layout } from 'antd';
import { DeleteOutlined, DownOutlined } from '@ant-design/icons';
import { useModel } from 'umi';
import FileInput from '@/components/common/fileInput';

import JSZip from 'jszip';
import type { FileMap } from '@/interfaces/file';
import {
  requestAssembleDataComponent,
  requestCreateDataFrame,
  requestDataComponentUploadInfo,
} from '@/request/data';
import { UploadFromType, UploadType } from '@/constants/data';
import { AnalysisType } from '@/constants/analysis';
import {
  requestDeleteDataComponent,
  requestUploadToAWS,
  uploadFileToAWS,
} from '@/request/awsOperation';
import { flatFileMap } from '@/util/fileTool';
import { requestImportDatas } from '@/request/analysis';

// const checkFolderStructure = (schema: RegExp[], fileList: string[]) => {
//   const missingFiles = schema.filter((file) => {
//     const found = fileList.find((f) => file.test(f));
//     return !found;
//   });

//   return [missingFiles.length === 0, missingFiles];
// };

const compareTreeDataAndFileMap = (treeData: any[], fileMap: FileMap | null | undefined) => {
  // Depth-first traversal visiting every leaf of treeData and recording missing keys
  const lackKeys: string[] = [];
  const dfs = (treeData: any[], fileMap: FileMap | null | undefined) => {
    let isLack = false;
    for (const node of treeData) {
      const key = node.key.split('/').at(-1);
      if (node.children) {
        const isSubLack = dfs(node.children, fileMap?.[key]?.children);
        if (isSubLack) {
          lackKeys.push(node.key);
          isLack = true;
        }
      } else {
        if (!fileMap?.[key]) {
          lackKeys.push(node.key);
          isLack = true;
        }
      }
    }
    return isLack;
  };
  dfs(treeData, fileMap);
  return lackKeys;
};

const modifyFileMap = (fileMap: FileMap, prefixList: string[], value: FileMap) => {
  const newFileMap = { ...fileMap };
  let ptr = newFileMap;
  if (prefixList.length === 0) {
    return { ...newFileMap, ...value };
  }
  for (let i = 0; i < prefixList.length; i++) {
    const prefix = prefixList[i];
    if (i === prefixList.length - 1) {
      ptr[prefix].children = {
        ...ptr[prefix].children,
        ...value,
      };
    } else {
      ptr = ptr[prefix].children;
    }
  }
  return newFileMap;
};

// const necessaryFileSchemas = [
//   /aggregation\.csv/,
//   /aggr_tissue_positions\.csv/,
//   /analysis\/clustering/,
//   /analysis\/diffexp/,
//   /analysis\/pca/,
//   /analysis\/tsne/,
//   /analysis\/umap/,
//   /cloupe\.cloupe/,
//   /filtered_feature_bc_matrix\/barcodes\.tsv\.gz/,
//   /filtered_feature_bc_matrix\/features\.tsv\.gz/,
//   /filtered_feature_bc_matrix\/matrix\.mtx\.gz/,
//   /filtered_feature_bc_matrix\.h5/,
//   /spatial\/[A-Za-z0-9]+\/scalefactors_json\.json/,
//   /spatial\/[A-Za-z0-9]+\/tissue_hires_image\.png/,
//   /spatial\/[A-Za-z0-9]+\/tissue_lowres_image\.png/,
//   /summary\.json/,
//   /web_summary\.html/,
// ];

const initNecessaryFilesTreeData = [
  {
    title: (
      <span>
        outs <span style={{ color: 'red' }}>*</span>
      </span>
    ),
    key: 'root',
    children: [
      {
        title: 'aggregation.csv',
        key: 'aggregation.csv',
      },
      {
        title: 'aggr_tissue_positions.csv',
        key: 'aggr_tissue_positions.csv',
      },
      {
        title: 'analysis',
        key: 'analysis',
        children: [
          {
            title: 'clustering',
            key: 'analysis/clustering',
          },
          {
            title: 'diffexp',
            key: 'analysis/diffexp',
          },
          {
            title: 'pca',
            key: 'analysis/pca',
          },
          {
            title: 'tsne',
            key: 'analysis/tsne',
          },
          {
            title: 'umap',
            key: 'analysis/umap',
          },
        ],
      },
      {
        title: 'cloupe.cloupe',
        key: 'cloupe.cloupe',
      },
      {
        title: 'filtered_feature_bc_matrix',
        key: 'filtered_feature_bc_matrix',
        children: [
          {
            title: 'barcodes.tsv.gz',
            key: 'filtered_feature_bc_matrix/barcodes.tsv.gz',
          },
          {
            title: 'features.tsv.gz',
            key: 'filtered_feature_bc_matrix/features.tsv.gz',
          },
          {
            title: 'matrix.mtx.gz',
            key: 'filtered_feature_bc_matrix/matrix.mtx.gz',
          },
        ],
      },
      {
        title: 'filtered_feature_bc_matrix.h5',
        key: 'filtered_feature_bc_matrix.h5',
      },
      {
        title: 'spatial',
        key: 'spatial',
        children: [
          {
            title: '[A]',
            key: 'spatial/[A]',
            children: [
              {
                title: 'scalefactors_json.json',
                key: 'spatial/[A]/scalefactors_json.json',
              },
              {
                title: 'tissue_hires_image.png',
                key: 'spatial/[A]/tissue_hires_image.png',
              },
              {
                title: 'tissue_lowres_image.png',
                key: 'spatial/[A]/tissue_lowres_image.png',
              },
            ],
          },
        ],
      },
      {
        title: 'summary.json',
        key: 'summary.json',
      },
      {
        title: 'web_summary.html',
        key: 'web_summary.html',
      },
    ],
  },
];

const Step = {
  BASIC: 'basic',
  UPLOAD: 'upload',
  COMPLETE: 'complete',
};

const getNextStep = (currentStep: string) => {
  switch (currentStep) {
    case Step.BASIC:
      return Step.UPLOAD;
    case Step.UPLOAD:
      return Step.COMPLETE;
    case Step.COMPLETE:
      return Step.BASIC;
    default:
      return Step.BASIC;
  }
};

const SpaceRangerAggr = () => {
  const { analysisAccessType } = useModel('analysis');
  const { targetAnalysisId, closeUploadDataUI } = useModel('uploadDataUI');
  const { isGuest } = useModel('user');
  const [form] = Form.useForm();
  const [step, setStep] = useState(Step.BASIC);
  const [dataFrameId, setDataFrameId] = useState<string | null>(null);
  const [fileMap, setFileMap] = useState<FileMap | null>(null);
  const [treeData, setTreeData] = useState<any[]>(initNecessaryFilesTreeData);
  const [prefixList, setPrefixList] = useState<string[]>([]);
  const [s3Prefix, setS3Prefix] = useState<string>('');
  const [lackKeys, setLackKeys] = useState<string[]>([]);
  const [processMap, setProcessMap] = useState<Record<string, number>>({});
  const [assembling, setAssembling] = useState<boolean>(false);
  const isGuestUser = isGuest();

  useEffect(() => {
    const prefixStr = 's3-store/' + (prefixList.length > 0 ? prefixList.join('/') + '/' : '');
    setS3Prefix(prefixStr);
  }, [prefixList]);

  const submitBasicDataInfo = async () => {
    const values = await form.validateFields();
    const { data: dataFrame } = await requestCreateDataFrame(
      UploadFromType.FROM_SPACERANGER_COUNT,
      values.name,
      UploadType.SPACERANGER_COUNT,
      values.species,
      values.description,
    );
    setDataFrameId(dataFrame.id);
    setStep(getNextStep(step));
  };

  const startUpload = async (componentKey: string, file: File) => {
    const controller = new AbortController();
    const { data: uploadInfo } = await requestDataComponentUploadInfo(
      dataFrameId as string,
      componentKey,
      '',
      UploadType.SPACERANGER_COUNT,
      file.size,
    );
    if (uploadInfo.multipart) {
      await requestUploadToAWS(
        file,
        uploadInfo.partInfoList,
        uploadInfo.part_count,
        uploadInfo.part_size,
        uploadInfo.object_key,
        uploadInfo.uploadId,
        (progress: number) => {
          setProcessMap((prev) => {
            return {
              ...prev,
              [componentKey]: progress,
            };
          });
        },
      );
    } else {
      await uploadFileToAWS(file, uploadInfo.presigned_url, controller, (progress: number) => {
        setProcessMap((prev) => {
          return {
            ...prev,
            [componentKey]: progress,
          };
        });
      });
    }
  };

  const startUploadFolder = async (fileMap: FileMap | null, prefix: string = null) => {
    if (!fileMap) return {};
    const flattenFm = flatFileMap(fileMap);
    console.log(flattenFm);
    const keys = Object.keys(flattenFm);
    keys.forEach((key) => {
      const fileItem = flattenFm[key];
      if (fileItem.type === 'file') {
        startUpload(`s3-store/${prefix ? prefix : ''}${key}`, fileItem.file as File);
      }
    });
  };

  const onFilesChange = async (_nfm: FileMap) => {
    let newFileMap = _nfm;
    const fileMapFirstLevelNames = Object.keys(newFileMap);
    if (fileMapFirstLevelNames.length === 0) {
      return;
    }
    if (fileMapFirstLevelNames.length === 1) {
      const onlyFName = fileMapFirstLevelNames[0];
      const onlyFileItem = newFileMap[fileMapFirstLevelNames[0]];
      console.log('old fileMap:', fileMap);
      console.log('new fileMap:', newFileMap);
      if ((!fileMap || Object.keys(fileMap).length === 0) && onlyFileItem.type === 'folder') {
        const newFm = onlyFileItem.children;
        startUploadFolder(newFm);
        setFileMap(newFm);
        return;
      }
      if ((!fileMap || Object.keys(fileMap).length === 0) && onlyFName.endsWith('.zip')) {
        const zip = new JSZip();
        const zipContent = await zip.loadAsync(onlyFileItem.file);
        const filePaths = Object.keys(zipContent.files);
        const files = await Promise.all(
          filePaths.map(async (filePath) => {
            const file = zipContent.files[filePath];
            const innerPath = filePath.split('/').slice(1).join('/');
            if (file.dir)
              return {
                filePath: innerPath,
                file: null,
                type: 'folder',
              };
            const fileData = await file.async('blob');
            return {
              filePath: innerPath,
              file: new File([fileData], innerPath),
              type: 'file',
            };
          }),
        );
        files.forEach(({ filePath, type, file }) => {
          if (type === 'folder') {
            return;
          }
          startUpload(`s3-store/${filePath}`, file as File);
        });
        newFileMap = files.reduce((acc, { type, filePath }, index) => {
          if (type === 'folder') return acc;
          let _acc = acc;
          const path = filePath.split('/');
          path.forEach((p, i) => {
            if (i === path.length - 1) {
              _acc[p] = files[index];
            } else {
              if (!_acc[p]) {
                _acc[p] = {
                  type: 'folder',
                  children: {},
                };
              }
              _acc = _acc[p].children;
            }
          });
          return acc;
        }, {});
        setFileMap(newFileMap);
        return;
      }
    }
    const prefixStr = prefixList.length > 0 ? prefixList.join('/') + '/' : '';
    startUploadFolder(newFileMap, prefixStr);
    newFileMap = modifyFileMap(fileMap, prefixList, newFileMap);
    setFileMap(newFileMap);
  };

  const assembleData = async () => {
    console.log('lackKeys', lackKeys);
    if (lackKeys.length > 0) {
      message.error('Some necessary files are missing');
      return;
    }
    if (dataFrameId === null) {
      return;
    }
    setAssembling(true);
    try {
      await requestAssembleDataComponent(dataFrameId);
      if (targetAnalysisId !== null) {
        await requestImportDatas(targetAnalysisId, [dataFrameId]);
      }
      message.success('Assemble data successfully');
    } catch (e: any) {
      message.error(e.message);
    }
    setAssembling(false);
    closeUploadDataUI();
  };

  const refreshLackKeys = () => {
    const lackedKeys = compareTreeDataAndFileMap(treeData[0].children, fileMap);
    setLackKeys(lackedKeys);
  };

  const updateNeccessaryFilesTreeData = () => {
    if (!fileMap || !fileMap.spatial || !fileMap.spatial.children) {
      return initNecessaryFilesTreeData;
    }

    const spatialChildren = fileMap.spatial.children;
    const spatialKeys = Object.keys(spatialChildren);
    const newSpatialTreeBranchData = spatialKeys.map((key) => {
      return {
        title: key,
        key: 'spatial/' + key,
        children: [
          {
            title: 'scalefactors_json.json',
            key: 'spatial/' + key + '/scalefactors_json.json',
          },
          {
            title: 'tissue_hires_image.png',
            key: 'spatial/' + key + '/tissue_hires_image.png',
          },
          {
            title: 'tissue_lowres_image.png',
            key: 'spatial/' + key + '/tissue_lowres_image.png',
          },
        ],
      };
    });
    const newTreeData = [...initNecessaryFilesTreeData];
    newTreeData[0].children[6].children = newSpatialTreeBranchData;
    setTreeData(newTreeData);
  };

  const deleteFile = async (key: string) => {
    const componentType = s3Prefix + key;
    await requestDeleteDataComponent(dataFrameId, componentType);
    const fileMapCopy = { ...fileMap };
    let ptr = fileMapCopy;
    if (prefixList.length === 0) {
      delete ptr[key];
      setFileMap(fileMapCopy);
      return;
    }
    for (let i = 0; i < prefixList.length; i++) {
      const prefix = prefixList[i];
      if (i === prefixList.length - 1) {
        if (ptr[prefix].children) {
          delete ptr[prefix].children[key];
        }
      } else {
        ptr = ptr[prefix].children;
      }
    }
    setFileMap(fileMapCopy);
  };

  useEffect(() => {
    updateNeccessaryFilesTreeData();
  }, [fileMap]);

  useEffect(() => {
    refreshLackKeys();
  }, [fileMap, treeData]);

  if (step === Step.BASIC) {
    return (
      <Layout>
        <Layout.Content
          style={{
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'stretch',
            maxHeight: '60vh',
            overflow: 'auto',
          }}
        >
          <h3>Space Ranger</h3>
          <BasicDataInfoForm form={form} showName />
        </Layout.Content>

        <Layout.Footer
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <Button
            type="primary"
            size="large"
            onClick={submitBasicDataInfo}
            disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC}
          >
            Next
          </Button>
        </Layout.Footer>
      </Layout>
    );
  }

  const fileMapPtr =
    prefixList.reduce((acc: FileMap, prefix: string) => {
      return acc[prefix].children || {};
    }, fileMap) || {};

  if (step === Step.UPLOAD) {
    return (
      <div
        style={{
          height: '60vh',
          backgroundColor: 'white',
          border: '1px solid #e0e0e0',
        }}
      >
        <Row
          style={{
            height: '50vh',
            borderBottom: '1px solid #e0e0e0',
          }}
        >
          <Col
            span={12}
            style={{
              height: '50vh',
              borderRight: '1px solid #e0e0e0',
            }}
          >
            <div
              style={{
                height: '25vh',
                borderBottom: '1px solid #e0e0e0',
              }}
            >
              <div
                style={{
                  height: '25vh',
                }}
              >
                <FileInput
                  triggers={['drop', 'click']}
                  onChange={onFilesChange}
                  disabled={analysisAccessType !== AnalysisType.PUBLIC}
                />
              </div>
            </div>
            <div
              style={{
                height: '25vh',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div
                style={{
                  height: '3em',
                  lineHeight: '3em',
                  paddingLeft: '1em',
                  borderBottom: '1px solid #e0e0e0',
                }}
              >
                <span
                  key={'root'}
                  style={{
                    color: '#1890ff',
                    cursor: 'pointer',
                  }}
                  onClick={() => {
                    setPrefixList([]);
                  }}
                >
                  root
                </span>{' '}
                /
                {prefixList.map((prefix) => (
                  <span key={prefix}>
                    {' '}
                    <span
                      key={prefix}
                      style={{
                        color: '#1890ff',
                        cursor: 'pointer',
                      }}
                      onClick={() => {
                        setPrefixList(prefixList.slice(0, prefixList.indexOf(prefix) + 1));
                      }}
                    >
                      {prefix}
                    </span>{' '}
                    /
                  </span>
                ))}
              </div>
              <div
                style={{
                  flex: 1,
                  overflow: 'auto',
                }}
              >
                {Object.keys(fileMapPtr).map((key) => {
                  const fileItem = fileMapPtr[key];
                  if (!fileItem) return null;
                  const isFolder = fileItem.type === 'folder';
                  const processKey = s3Prefix + key;
                  const process = processMap[processKey];
                  return (
                    <div
                      key={key}
                      style={{
                        height: '2em',
                        lineHeight: '2em',
                        paddingLeft: '1em',
                        paddingRight: '1em',
                        // borderBottom: '1px solid #e0e0e0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-start',
                      }}
                      onClick={() => {
                        if (isFolder) {
                          setPrefixList([...prefixList, key]);
                        }
                      }}
                    >
                      <span
                        style={{
                          color: isFolder ? '#1890ff' : '#555',
                          cursor: isFolder ? 'pointer' : 'default',
                        }}
                      >
                        {key} {isFolder ? '/' : ''}
                      </span>
                      <div
                        style={{
                          flex: 1,
                        }}
                      />
                      {!isFolder && (!process || process < 99) && (
                        <span>{process ? `${process}%` : '0%'}</span>
                      )}
                      {process >= 99 && (
                        <Button
                          icon={<DeleteOutlined style={{ color: '#bbb' }} />}
                          size="small"
                          type="text"
                          onClick={() => {
                            deleteFile(key);
                          }}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </Col>
          <Col
            span={12}
            style={{
              overflow: 'auto',
              height: '49vh',
            }}
          >
            <Tree
              showLine
              defaultExpandAll
              switcherIcon={<DownOutlined />}
              defaultExpandedKeys={['0-0-0']}
              onSelect={(selectedInfo: any) => console.log(selectedInfo)}
              treeData={treeData}
              titleRender={(nodeData: any) => {
                const { title, key } = nodeData;
                if (key === 'root') {
                  return <span>root</span>;
                }
                const isLack = lackKeys.includes(key);
                return (
                  <span
                    style={{
                      color: isLack ? '#aaa' : '#333',
                    }}
                  >
                    {title}
                  </span>
                );
              }}
            />
          </Col>
        </Row>
        <div
          style={{
            height: '10vh',
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            paddingRight: '2rem',
          }}
        >
          {/* <Button
            type="primary"
            onClick={() => {
              setStep(getPrevStep(step));
            }}
          >
            Prev
          </Button> */}
          <Button type="primary" onClick={assembleData} loading={assembling}>
            assemble
          </Button>
        </div>
      </div>
    );
  }

  if (step === Step.COMPLETE) {
    return (
      <div>
        <h1>Complete</h1>
      </div>
    );
  }
};

export default SpaceRangerAggr;
