import { DeleteOutlined, EditOutlined } from '@ant-design/icons';
import {
  Button,
  Form as AntForm,
  Form,
  Input as AntInput,
  Input,
  Layout,
  message,
  Modal,
  Popover,
  Space,
  Table,
  Tooltip,
  Upload,
} from 'antd';
import type { FormInstance } from 'antd/es/form';
import React, { useContext, useEffect, useRef, useState } from 'react';
import styles from './outs.less';
import { AnalysisType } from '@/constants/analysis';
import BasicDataInfoForm from './basicDataInform';
import { UploadFromType, UploadType } from '@/constants/data';
import {
  requestAssembleDataComponent,
  requestCreateDataFrame,
  requestDataComponentUploadInfo,
  requestValidateUpdate,
} from '@/request/data';
import { useModel } from 'umi';
import { ServiceCloudSelection } from '@/constants/serviceCloudSelection';
import { ServiceCloud } from '@/constants';
import { requestImportDatas } from '@/request/analysis';
import {
  requestUploadToAWS,
  uploadFileToAWS,
  requestDeleteDataComponent,
  requestEditFileInAWS,
} from '@/request/awsOperation';

function UploadFileComponent({ record, onSave, text, process }) {
  const [fileList, setFileList] = useState<[{ name: string }] | []>([]);

  useEffect(() => {
    if (record[text] !== 'Update') {
      setFileList([{ name: record[text] }]);
    }
  }, [record]);
  const onFileChange = (info) => {
    const { file } = info;
    // onSave(file); // Invoke the callback to save the data

    // File uploaded successfully; handle post-upload logic here
    // e.g. save the file info into the data source

    record[text] = file.name;
    setFileList([{ name: file.name }]);
    const newRecord = { ...record, text: text };
    onSave(newRecord, file); // Invoke the callback to save the data
  };

  if (process !== undefined) {
    return (
      <div>
        <div style={{ color: '#5664B3' }}>Uploading...</div>
        <div>{process}%</div>
      </div>
    );
  }

  return (
    <Upload
      name="file"
      multiple={false}
      maxCount={1}
      onChange={onFileChange}
      fileList={fileList}
      beforeUpload={() => false}
      accept=".tsv,.mtx"
      showRemoveIcon={false}
    >
      <div style={{ color: '#5664B3', cursor: 'pointer' }}>Upload</div>
    </Upload>
  );
}
const EditForm = (props) => {
  const { item, onSubmit } = props;
  const { dictionary } = useModel('localization');

  const onFinish = async (values: any) => {
    await onSubmit(item.key, values);
  };

  return (
    <Form
      name="basic"
      labelCol={{ span: 8 }}
      wrapperCol={{ span: 16 }}
      style={{ maxWidth: 600 }}
      initialValues={{ remember: true }}
      onFinish={onFinish}
      autoComplete="off"
    >
      <Form.Item label="sample" name="sample" initialValue={item.sample}>
        <Input />
      </Form.Item>

      <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
        <Button type="primary" htmlType="submit">
          {dictionary.SUBMIT}
        </Button>
      </Form.Item>
    </Form>
  );
};

type EditableTableProps = Parameters<typeof Table>[0];
type ColumnTypes = Exclude<EditableTableProps['columns'], undefined>;
const EditableContext = React.createContext<FormInstance<any> | null>(null);
const EditableRow = ({ index, ...props }) => {
  const [form] = AntForm.useForm();
  return (
    <AntForm form={form} component={false}>
      <EditableContext.Provider value={form}>
        <tr {...props} />
      </EditableContext.Provider>
    </AntForm>
  );
};

const EditableCell = ({
  title,
  editable,
  children,
  dataIndex,
  record,
  handleSave,
  ...restProps
}) => {
  const [editing, setEditing] = useState(false);
  const inputRef = useRef(null);
  const form = useContext(EditableContext);
  useEffect(() => {
    if (editing) {
      inputRef.current.focus();
    }
  }, [editing]);

  const toggleEdit = () => {
    setEditing(!editing);
    form.setFieldsValue({
      [dataIndex]: record[dataIndex],
    });
  };

  const save = async () => {
    try {
      const values = await form.validateFields();
      toggleEdit();

      handleSave({ ...record, ...values }, dataIndex);
    } catch (errInfo) {
      console.error('Save failed:', errInfo);
    }
  };

  let childNode = children;

  if (editable) {
    childNode = editing ? (
      <AntForm.Item
        style={{
          margin: 0,
        }}
        name={dataIndex}
      >
        <AntInput ref={inputRef} onPressEnter={save} onBlur={save} />
      </AntForm.Item>
    ) : (
      <div
        className={styles.editableCellValueWrap}
        style={{
          paddingRight: 24,
        }}
        onClick={toggleEdit}
      >
        {children}
      </div>
    );
  }

  return <td {...restProps}>{childNode}</td>;
};

interface DataSourceItem {
  key: string;
  sample: string;
  barcodes: string;
  genes: string;
  matrix: string;
  isUpdate: boolean;
}
function Outs() {
  const [dataSource, setDataSource] = useState<DataSourceItem[]>([]);
  const [uploadingProcessDict, setUploadingProcessDict] = useState<Record<string, number>>({}); // upload progress
  const [addColModal, setAddColModal] = useState(false);
  // const [colTitle, setColTitle] = useState({ name: '' });
  const [editTableColumns, setEditTableColumns] = useState<any>([]);
  const [deleteKey, setDeleteKey] = useState(null);
  const [editKey, setEditKey] = useState({ name: '' });
  const [columnsNameForm] = Form.useForm();
  const [rowNameForm] = Form.useForm();
  const [showPage, setShowPage] = React.useState(false);
  const [showSampleName, setShowSampleName] = React.useState(false);
  const [form] = Form.useForm();
  const [assembleLoading, setAssembleLoading] = React.useState(false);
  const [assemblable, setAssemblable] = React.useState(false);
  // const [species, setSpecies] = React.useState(null as null | string);

  const {
    data10xId,
    setData10xId,
    targetAnalysisId,
    closeUploadDataUI,
    uploaded10xFileList,
    setUploaded10xFileList,
  } = useModel('uploadDataUI');

  const { dictionary } = useModel('localization');
  const { analysisAccessType } = useModel('analysis');
  const { isGuest } = useModel('user');
  const isGuestUser = isGuest();

  // Subscribe to column deletion
  useEffect(() => {
    if (deleteKey !== null) {
      // Remove the column name
      const columnsData = [...editTableColumns];
      setEditTableColumns(columnsData.filter((item) => item.dataIndex !== deleteKey));
      // Remove the column data
      const dataSourceData = [...dataSource];
      for (const element of dataSourceData) {
        delete element[deleteKey];
      }
      setDataSource(dataSourceData);
    }
  }, [deleteKey]);

  useEffect(() => {
    const isDataComplete =
      dataSource.every((item) => {
        return item.matrix !== 'Update' && item.barcodes !== 'Update' && item.genes !== 'Update';
      }) && Object.keys(uploadingProcessDict).length === 0;
    setAssemblable(isDataComplete);
  }, [dataSource, uploadingProcessDict]);
  // Subscribe to column editing
  useEffect(() => {
    if (editKey.name !== '') {
      // setColTitle({ name: editKey.name });
      setAddColModal(true);
    }
  }, [editKey]);
  // Clear data when the modal is closed
  useEffect(() => {
    if (addColModal === false) {
      // setColTitle({ name: '' });
      setDeleteKey(null);
      setEditKey({ name: '' });
    }
  }, [addColModal]);

  const components = {
    body: {
      row: EditableRow,
      cell: EditableCell,
    },
  };
  const handleFileByUpdate = async (row, file) => {
    if (ServiceCloud == ServiceCloudSelection.AWS) {
      try {
        const fileSuffix = file.name.substring(file.name.lastIndexOf('.') + 1);
        const componentType = `${row.sample}-${row.text}`;
        const { data: uploadInfo } = await requestDataComponentUploadInfo(
          data10xId as string,
          componentType,
          fileSuffix,
          UploadType.OUTS,
          1,
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
              setUploadingProcessDict(() => {
                return { ...uploadingProcessDict, [componentType]: progress };
              });
            },
          );
        } else {
          await uploadFileToAWS(file, uploadInfo.presigned_url, null, (progress: number) => {
            setUploadingProcessDict(() => {
              return { ...uploadingProcessDict, [componentType]: progress };
            });
          });
        }

        setUploadingProcessDict((preDict) => {
          const newDict = { ...preDict };
          delete newDict[componentType];
          return newDict;
        });

        uploaded10xFileList.push({
          dataId: data10xId,
          categoryName: componentType,
        });
        setUploaded10xFileList(uploaded10xFileList);
        const newData = [...dataSource];
        const index = newData.findIndex((item) => row.key === item.key);
        const item = newData[index];
        newData.splice(index, 1, { ...item, ...row });
        setDataSource(newData);
      } catch (error) {
        console.error(error);
      }
    }
  };

  async function handleEdit(key, value) {
    for (const i of dataSource) {
      if (i.sample == value.sample) {
        message.warning('name cannot be duplicate!');
        return;
      }
    }
    // Find the data row matching the clicked row's unique identifier (key)
    if (value) {
      const deleteFilePromises = uploaded10xFileList.map((file) => {
        const objectKeyList = file.categoryName.split('-');

        // Check whether the key contains '-1-'
        if (objectKeyList[0] === key) {
          const newBucketName = file.categoryName.replace(
            new RegExp(`${key}-`),
            `${value.sample}-`,
          );

          // Return a Promise
          return requestEditFileInAWS(file.dataId, file.categoryName, newBucketName);
        } else {
          // If it does not contain '-1-', return a resolved Promise
          return Promise.resolve();
        }
      });

      Promise.all(deleteFilePromises)
        .then(() => {
          const newUploaded10xFileList = uploaded10xFileList.map((file) => {
            const objectKeyList = file.categoryName.split('-');
            // Check whether the key contains '-1-'
            if (objectKeyList[0] === key) {
              const newBucketName = file.categoryName.replace(
                new RegExp(`${key}-`),
                `${value.sample}-`,
              );
              file.categoryName = newBucketName;
              return file;
              // Return a Promise
            } else {
              return file;
            }
          });

          setUploaded10xFileList(newUploaded10xFileList);

          const updatedDataSource = dataSource.map((record) => {
            if (record.key === key) {
              // Set this row's data to the editable state (adjust to your data structure)
              for (const i of dataSource) {
                if (i.sample == value.sample) {
                  return record;
                }
              }

              record.key = value.sample;
              record.sample = value.sample;

              return record;
            } else {
              return record;
            }
          });
          // Update the component data source to trigger a re-render and make the row editable
          setDataSource(updatedDataSource);
        })
        .catch((error) => {
          console.error('Error deleting objects:', error);
        });
    }
  }

  const handleDelete = async (key) => {
    const deleteFilePromises = uploaded10xFileList.map((file) => {
      const objectKeyList = file.categoryName.split('-');

      // Check whether the key contains '-1-'
      if (objectKeyList[0] === key) {
        // Return a Promise
        return requestDeleteDataComponent(file.dataId, file.categoryName);
      } else {
        // If it does not contain '-1-', return a resolved Promise
        return Promise.resolve();
      }
    });

    // Use Promise.all to run the deletions in parallel
    Promise.all(deleteFilePromises)
      .then(() => {
        const newUploaded10xFileList = uploaded10xFileList.filter((file) => {
          const objectKeyList = file.categoryName.split('-');
          return objectKeyList[0] !== key;
        });
        setUploaded10xFileList(newUploaded10xFileList);
        const editTableDataSource = [...dataSource];
        setDataSource(editTableDataSource.filter((item) => item.key !== key));
      })
      .catch((error) => {
        console.error('Error deleting objects:', error);
      });
  };

  const handleSave = async (row, categoryName) => {
    if (ServiceCloud == ServiceCloudSelection.AWS && data10xId) {
      try {
        const componentType = `${row.sample}-custome_category_${categoryName}`;

        const { data: uploadInfo } = await requestDataComponentUploadInfo(
          data10xId as string,
          componentType,
          '',
          UploadType.OUTS,
          1,
        );
        if (uploadInfo.multipart) {
          await requestUploadToAWS(
            row[categoryName],
            uploadInfo.partInfoList,
            uploadInfo.part_count,
            uploadInfo.part_size,
            uploadInfo.object_key,
            uploadInfo.uploadId,
            (progress: number) => {
              return progress;
            },
          );
        } else {
          await uploadFileToAWS(
            row[categoryName],
            uploadInfo.presigned_url,
            null,
            (progress: number) => {
              return progress;
            },
          );
        }
        const newData = [...dataSource];
        const index = newData.findIndex((item) => row.key === item.key);
        const item = newData[index];
        newData.splice(index, 1, { ...item, ...row });
        setDataSource(newData);

        // Check whether uploaded10xFileList contains the given key
        const keyExists = uploaded10xFileList.some((file) => {
          const objectKeyList = file.categoryName.split('-');
          const objectKey = objectKeyList[objectKeyList.length - 1];
          // Check whether the key contains '-1-'

          return objectKey == `custome_category_${categoryName}`;
        });

        if (!keyExists) {
          // If the key does not exist, do the following
          uploaded10xFileList.push({
            dataId: data10xId,
            categoryName: componentType,
          });
          setUploaded10xFileList(uploaded10xFileList); // Use a new array to trigger a React re-render
        }
      } catch (error) {
        console.error(error);
      }
    }
  };

  // Initial columns
  const columns: (ColumnTypes[number] & { editable?: boolean; dataIndex: string })[] = [
    {
      title: 'Sample',
      dataIndex: 'sample',
      width: 200,
      render: (text, record) => (
        <div>
          {text}
          <Popover
            title={'Edit data information'}
            content={<EditForm item={record} onSubmit={handleEdit} />}
          >
            <Button icon={<EditOutlined />} type="link" />
          </Popover>
          <Button icon={<DeleteOutlined />} type="link" onClick={() => handleDelete(record.key)} />
        </div>
      ),
      // editable: true,
    },
    {
      title: 'barcodes.tsv',
      dataIndex: 'barcodes',
      key: 'barcodes',
      width: 100,
      render: (text, record) => {
        if (record.isUpdate) {
          return (
            <UploadFileComponent
              text="barcodes"
              record={record} // Pass the current row data to the upload component
              onSave={handleFileByUpdate} // Callback invoked after a successful upload
              process={uploadingProcessDict[`${record.sample}-barcodes`]}
            />
          );
        }
        return text; // Display the "Update" text
      },
    },
    {
      title: 'genes.tsv',
      dataIndex: 'genes',
      key: 'genes',
      width: 100,
      render: (text, record) => {
        if (record.isUpdate) {
          return (
            <UploadFileComponent
              text="genes"
              record={record} // Pass the current row data to the upload component
              onSave={handleFileByUpdate} // Callback invoked after a successful upload
              process={uploadingProcessDict[`${record.sample}-genes`]}
            />
          );
        }
        return text; // Display the "Update" text
      },
    },
    {
      title: 'matrix.mtx',
      dataIndex: 'matrix',
      key: 'matrix',
      width: 100,
      render: (text, record) => {
        if (record.isUpdate) {
          return (
            <UploadFileComponent
              text="matrix"
              record={record} // Pass the current row data to the upload component
              onSave={handleFileByUpdate} // Callback invoked after a successful upload
              process={uploadingProcessDict[`${record.sample}-matrix`]}
            />
          );
        }
        return text; // Display the "Update" text
      },
    },
  ].concat(
    editTableColumns.map((col) => {
      if (!col.editable) {
        return col;
      }
      return {
        ...col,
        onCell: (record) => ({
          record,
          editable: col.editable,
          dataIndex: col.dataIndex,
          title: col.title,
          handleSave: handleSave,
        }),
      };
    }),
  );

  const handleAdd = async (name) => {
    if (ServiceCloud == ServiceCloudSelection.AWS && data10xId) {
      const componentType = `${name}-sample_placeholder`;

      try {
        const { data: uploadInfo } = await requestDataComponentUploadInfo(
          data10xId as string,
          componentType,
          '',
          UploadType.OUTS,
          1,
        );
        if (uploadInfo.multipart) {
          await requestUploadToAWS(
            name,
            uploadInfo.partInfoList,
            uploadInfo.part_count,
            uploadInfo.part_size,
            uploadInfo.object_key,
            uploadInfo.uploadId,
            (progress: number) => {
              return progress;
            },
          );
        } else {
          await uploadFileToAWS(name, uploadInfo.presigned_url, null, (progress: number) => {
            return progress;
          });
        }
        uploaded10xFileList.push({
          dataId: data10xId,
          categoryName: componentType,
        });
        setUploaded10xFileList(uploaded10xFileList);
        const newData = {
          key: `${name}`,
          sample: `${name}`,
          barcodes: 'Update',
          genes: 'Update',
          matrix: 'Update',
          isUpdate: true,
        };
        if (dataSource.length === 0) {
          setDataSource([newData]);
        } else {
          setDataSource([...dataSource, newData]);
        }
        message.success('Upload successfully.');
      } catch (err) {
        console.error(err);
      }
    }
  };

  const deleteCategoryCol = async (key) => {
    const deleteFilePromises = uploaded10xFileList.map((file) => {
      const objectKeyList = file.categoryName.split('-');
      const objectKey = objectKeyList[objectKeyList.length - 1];
      const list = objectKey.split('_');
      // Check whether the key contains '-1-'
      if (list[list.length - 1] == key) {
        // Return a Promise
        try {
          return requestDeleteDataComponent(file.dataId, file.categoryName);
        } catch {
          console.error('delete failed');
        }
      } else {
        // If it does not contain '-1-', return a resolved Promise
        return Promise.resolve();
      }
    });

    // Use Promise.all to run the deletions in parallel
    Promise.all(deleteFilePromises)
      .then(() => {
        const newUploaded10xFileList = uploaded10xFileList.filter((file) => {
          const objectKeyList = file.categoryName.split('-');
          const objectKey = objectKeyList[objectKeyList.length - 1];
          const list = objectKey.split('_');

          // Check whether the key contains '-1-'
          return list[list.length - 1] != key;
        });

        setUploaded10xFileList(newUploaded10xFileList);
        setDeleteKey(null);
      })
      .catch((error) => {
        console.error('Error deleting objects:', error);
      });
  };

  const EditCategoryCol = async (oldName, newName) => {
    const deleteFilePromises = uploaded10xFileList.map((file) => {
      const objectKeyList = file.categoryName.split('-');
      const objectKey = objectKeyList[objectKeyList.length - 1];
      const list = objectKey.split('_');
      // Check whether the key contains '-1-'

      if (list[list.length - 1] == oldName) {
        const newBucketName = file.categoryName.replace(
          new RegExp(`custome_category_${oldName}`),
          `custome_category_${newName}`,
        );
        // Return a Promise
        return requestEditFileInAWS(file.dataId, file.categoryName, newBucketName);
      } else {
        // If it does not contain '-1-', return a resolved Promise
        return Promise.resolve();
      }
    });

    // Use Promise.all to run the deletions in parallel
    Promise.all(deleteFilePromises)
      .then(() => {
        const newUploaded10xFileList = uploaded10xFileList.map((file) => {
          const objectKeyList = file.categoryName.split('-');
          const objectKey = objectKeyList[objectKeyList.length - 1];
          const list = objectKey.split('_');
          if (list[list.length - 1] == oldName) {
            const newBucketName = file.categoryName.replace(
              new RegExp(`custome_category_${oldName}`),
              `custome_category_${newName}`,
            );
            file.categoryName = newBucketName;
            return file;
            // Return a Promise
          } else {
            return file;
          }
        });
        setUploaded10xFileList(newUploaded10xFileList);
        setEditKey({ name: '' });
      })
      .catch((error) => {
        console.error('Error deleting objects:', error);
      });
  };

  useEffect(() => {
    if (deleteKey) {
      deleteCategoryCol(deleteKey);
    }
  }, [editTableColumns]);

  // Add a column
  function changeCol(colTitleName) {
    if (editKey.name === '') {
      setEditTableColumns((preState) => [
        {
          title: (
            <div style={{ display: 'flex', justifyContent: 'space-around' }}>
              <Tooltip title={colTitleName}>{colTitleName}</Tooltip>
              <div style={{ display: 'flex' }}>
                <div
                  name={colTitleName}
                  onClick={(e) => {
                    setEditKey({
                      name: e.currentTarget.getAttribute('name'),
                    });
                  }}
                >
                  <EditOutlined />
                </div>
                <div
                  style={{ marginLeft: '0.5vw' }}
                  name={colTitleName}
                  onClick={(e) => {
                    setDeleteKey(e.currentTarget.getAttribute('name'));
                    deleteCategoryCol(e.currentTarget.getAttribute('name'));
                  }}
                >
                  <DeleteOutlined />
                </div>
              </div>
            </div>
          ),
          dataIndex: colTitleName,
          width: '150px',
          render: (text) => (
            <div>
              {text}
              <Button icon={<EditOutlined />} type="link" />
            </div>
          ),
          editable: true,
        },
        ...preState,
      ]);

      const dataArrayData = dataSource.filter(() => true);
      for (const element of dataArrayData) {
        element[colTitleName] = '';
      }
      setDataSource(dataArrayData);
    } else {
      const dataArrayCol = editTableColumns.filter(() => true);
      EditCategoryCol(editKey.name, colTitleName);
      for (const element of dataArrayCol) {
        if (element.dataIndex === editKey.name) {
          element.dataIndex = colTitleName;
          element.title = (
            <div className="between">
              <div style={{ display: 'flex', justifyContent: 'space-around' }}>
                <Tooltip title={element.dataIndex}>{element.dataIndex}</Tooltip>
                <div style={{ display: 'flex' }}>
                  <div
                    name={element.dataIndex}
                    onClick={(e) => {
                      setEditKey({
                        name: e.currentTarget.getAttribute('name'),
                      });
                    }}
                    className="popover-content-edit"
                  >
                    <EditOutlined />
                  </div>
                  <div
                    style={{ marginLeft: '0.5vw' }}
                    name={element.dataIndex}
                    onClick={(e) => {
                      setDeleteKey(e.currentTarget.getAttribute('name'));
                      deleteCategoryCol(e.currentTarget.getAttribute('name'));
                    }}
                  >
                    <DeleteOutlined />
                  </div>
                </div>
              </div>
            </div>
          );
        }
      }
      setEditTableColumns(dataArrayCol);
      // Update the keys in the data
      if (colTitleName !== editKey.name) {
        const dataArrayData = dataSource.filter(() => true);
        for (const element of dataArrayData) {
          element[colTitleName] = element[editKey.name];
          delete element[editKey.name];
        }
        setDataSource(dataArrayData);
      }
    }
    setAddColModal(false);
  }

  function getColumns() {
    // const columnsData: (ColumnTypes[number] & { editable?: boolean; dataIndex: string })[] = [];
    const newColumnsData = columns.filter(() => true);

    // const allNewColumnData = columnsData.concat(newColumnsData);
    return newColumnsData;
  }

  // Merge
  const assembleData = async () => {
    if (data10xId === null) {
      message.error('Please upload component first');
      return;
    }
    setAssembleLoading(true);
    try {
      await requestAssembleDataComponent(data10xId);
      if (targetAnalysisId !== null) {
        await requestImportDatas(targetAnalysisId, [data10xId]);
      }
      message.success('10x out data successfully');
    } catch (e: any) {
      message.error(e.message);
    }
    setAssembleLoading(false);
    closeUploadDataUI();
  };

  return (
    <Layout>
      {!showPage && (
        <Layout.Content
          style={{
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'stretch',
            maxHeight: '55vh',
            overflow: 'auto',
          }}
        >
          <h3>10x out</h3>
          <BasicDataInfoForm form={form} showName={true} />
        </Layout.Content>
      )}
      {showPage && (
        <Layout.Content
          style={{
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'stretch',
            maxHeight: '55vh',
            overflow: 'auto',
          }}
        >
          <h3
            style={{
              paddingLeft: '10px',
            }}
          >
            10x out
          </h3>
          <div className="edit-page-param">
            <div
              style={{
                paddingLeft: '10px',
                paddingRight: '10px',
                paddingTop: '20px',
                paddingBottom: '20px',
              }}
            >
              <div style={{ fontSize: '16px', fontWeight: '600' }}>Description</div>
              <div>
                10x upload file instructions For each sample, please upload (barcodes.tsv.gz,
                features.tsv.gz, matrix.mtx.gz) in outs/filtered_feature_bc_matrix from 10x
                cellranger count outputs. Please refer to {''}
                <a href="https://support.10xgenomics.com/single-cell-gene-expression/software/pipelines/latest/output/matrices">
                  https://support.10xgenomics.com/single-cell-gene-expression/software/pipelines/latest/output/matrices
                </a>
                {''} for more information.
              </div>
              <div style={{ textAlign: 'left' }}>
                <div>
                  <Space>
                    <div
                      style={{
                        paddingTop: '5px',
                        paddingBottom: '5px',
                        marginTop: '10px',
                        marginBottom: '10px',
                        border: '1px solid #606cb7',
                        color: '#606cb7',
                        width: '150px',
                        textAlign: 'center',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        userSelect: 'none',
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        // handleAdd();
                        setShowSampleName(true);
                      }}
                    >
                      Add a sample
                    </div>
                    <div
                      style={{
                        paddingTop: '5px',
                        paddingBottom: '5px',
                        marginTop: '10px',
                        marginBottom: '10px',
                        border: '1px solid #606cb7',
                        color: '#606cb7',
                        width: '150px',
                        textAlign: 'center',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        userSelect: 'none',
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setAddColModal(true);
                      }}
                    >
                      Add a category
                    </div>
                  </Space>
                </div>
              </div>
              <div>
                <Table
                  components={components}
                  rowClassName={() => styles.editableRow}
                  dataSource={dataSource}
                  columns={getColumns()}
                  pagination={false}
                  scroll={{ x: '100%', y: 300 }}
                />
              </div>
              {/* Add column */}
              <Modal
                open={addColModal}
                closable={false}
                centered
                cancelText={dictionary.CANCEL}
                okText={dictionary.CONFIRM}
                onCancel={() => {
                  setAddColModal(false);
                  columnsNameForm.resetFields();
                }}
                onOk={async () => {
                  const { name } = columnsNameForm.getFieldsValue();

                  if (!name) {
                    message.warning('name is required!');
                    return;
                  }
                  // setColTitle({ name: name });
                  for (const key of columns) {
                    if (key.dataIndex === name) {
                      message.warning('name cannot be duplicate!');
                      return;
                    }
                  }

                  changeCol(name);
                  columnsNameForm.resetFields();
                }}
              >
                <Form form={columnsNameForm} autoComplete="off">
                  <Form.Item label="column name" name="name" rules={[{ required: true }]}>
                    <Input
                      placeholder="Column names may contain only letters, digits and underscores"
                      // onChange={(e) => {
                      //   setColTitle((preState) => ({ ...preState, name: e.target.value || '' }));
                      // }}
                    />
                  </Form.Item>
                </Form>
              </Modal>
              {/* Add sample */}
              <Modal
                open={showSampleName}
                closable={false}
                centered
                cancelText={dictionary.CANCEL}
                okText={dictionary.CONFIRM}
                onCancel={() => {
                  setShowSampleName(false);
                  rowNameForm.resetFields();
                }}
                onOk={async () => {
                  const { name } = rowNameForm.getFieldsValue();

                  if (!name) {
                    message.warning('name is required!');
                    return;
                  }

                  for (const i of dataSource) {
                    if (i.sample == name) {
                      message.warning('name cannot be duplicate!');
                      return;
                    }
                  }
                  handleAdd(name);
                  rowNameForm.resetFields();
                  setShowSampleName(false);
                }}
              >
                <Form form={rowNameForm} autoComplete="off">
                  <Form.Item label="sample name" name="name" rules={[{ required: true }]}>
                    <Input
                      placeholder="Column names may contain only letters, digits and underscores"
                      // onChange={(e) => {
                      //   setColTitle((preState) => ({ ...preState, name: e.target.value || '' }));
                      // }}
                    />
                  </Form.Item>
                </Form>
              </Modal>
            </div>
          </div>
        </Layout.Content>
      )}
      <Layout.Footer
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        {showPage && (
          <Button
            // type="primary"
            style={{ color: '#2949B0', border: '1px solid #5B74C3', marginRight: '1rem' }}
            onClick={() => {
              setShowPage(false);
            }}
            size="large"
          >
            {dictionary.PREVIOUS}
          </Button>
        )}
        {showPage && (
          <Button
            type="primary"
            size="large"
            disabled={!assemblable}
            loading={assembleLoading}
            onClick={assembleData}
          >
            {dictionary.ASSEMBLE}
          </Button>
        )}
        <div
          style={{
            width: '1rem',
          }}
        />

        {!showPage && (
          <Button
            type="primary"
            onClick={async () => {
              const { species, name, description } = await form.validateFields();
              if (species && name && description) {
                try {
                  await requestValidateUpdate(species, description);
                  const { data: result } = await requestCreateDataFrame(
                    UploadFromType.FROM10X,
                    name,
                    UploadType.OUTS,
                    species,
                    description,
                  );
                  if (result) {
                    setData10xId(result.id);
                  }
                  setShowPage(true);
                } catch (err) {
                  console.error('err', err);
                }
              }
            }}
            size="large"
            disabled={isGuestUser || analysisAccessType === AnalysisType.PUBLIC}
          >
            {dictionary.NEXT}
          </Button>
        )}
      </Layout.Footer>
    </Layout>
  );
}

export default Outs;
