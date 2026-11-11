import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';
import { DataListFetchMode, DataState } from '@/constants/data';
import { NodeType } from '@/constants/node';
import { AnalysisType } from '@/constants/analysis';
import type { DataType } from '@/interfaces/data';
import { requestDataSourceList } from '@/request/data';
import { getLocationParams } from '@/util/getUrl';
import { LoadingOutlined, PlusOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { AutoComplete, Dropdown, Menu, Button } from 'antd';
import React, { useEffect, useState } from 'react';
import { useModel } from 'umi';
import { DataTool } from '@/util/data';

const ImportSource = {
  DEVICE: 'upload from device',
  DATA_SOURCE: 'import from existing data',
  THIRD_PARTY_DATA: 'import from third party list',
};

const DataSource: React.FC = () => {
  const [analysisId] = getLocationParams(['analysis-id']);

  const { dictionary } = useModel('localization');

  const { openUploadDataUI } = useModel('uploadDataUI');

  const { openImportDataUI } = useModel('importDataUI');

  const { openErrorDataUI } = useModel('errorData');

  const { setIsThirdPartyDataListModalVisible: setThirdPartyDataSourceModalVisible } =
    useModel('thirdPartyDataSource');

  const { setDataCaptureModalVisible } = useModel('thirdPartyDataSource');

  const { analysisAccessType, importedDataSourceList } = useModel('analysis');

  const [publicDataSourceList, setPublicDataSourceList] = useState<DataType[]>([]);
  const [filteredPublicDataSourceList, setFilteredDisplayedDataSourceList] = useState<DataType[]>(
    [],
  );

  const [filteredImportedDataSourceList, setFilteredImportedDataSourceList] = useState<DataType[]>(
    [],
  );

  const [searchKey, setSearchKey] = useState('');

  const [wholeAutoCompleteOptions, setWholeAutoCompleteOptions] = useState<any[]>([]);
  const [autoCompleteOptions, setAutoCompleteOptions] = useState<any[]>([]);

  const [menuOpenKeys, setMenuOpenKeys] = useState<string[]>(['public', 'imported']);

  const loadPublicDataRelated = async () => {
    const { data: publicDataList } = await requestDataSourceList(
      DataListFetchMode.PUBLIC,
      null,
      null,
    );

    setPublicDataSourceList(publicDataList);
  };

  const loadAutoCompleteOptions = () => {
    const currentPublicDataList = publicDataSourceList || [];
    const currentImportedDataList = importedDataSourceList || [];

    const publicDataNames = currentPublicDataList.map((data: DataType) => data.name);
    const importedDataNames = currentImportedDataList.map((data: DataType) => data.name);

    const allDataNames = publicDataNames.concat(importedDataNames);
    // Deduplicate
    const uniqueDataNames = Array.from(new Set(allDataNames));
    setWholeAutoCompleteOptions(uniqueDataNames);
  };

  const filterDataList = () => {
    const currentPublicDataList = publicDataSourceList || [];
    const currentImportedDataList = importedDataSourceList || [];

    if (!searchKey) {
      setFilteredDisplayedDataSourceList(currentPublicDataList);
      setFilteredImportedDataSourceList(currentImportedDataList);
      return;
    }

    const filteredPublicDataList = currentPublicDataList.filter((data: DataType) =>
      data.name.includes(searchKey),
    );
    const filteredImportedDataList = currentImportedDataList.filter((data: DataType) =>
      data.name.includes(searchKey),
    );

    setFilteredDisplayedDataSourceList(filteredPublicDataList);
    setFilteredImportedDataSourceList(filteredImportedDataList);

    const keysToBeOpened: string[] = [...menuOpenKeys];
    if (filteredPublicDataList.length > 0 && !keysToBeOpened.includes('public')) {
      keysToBeOpened.push('public');
    }
    if (filteredImportedDataList.length > 0 && !keysToBeOpened.includes('imported')) {
      keysToBeOpened.push('imported');
    }
    setMenuOpenKeys(keysToBeOpened);
  };

  useEffect(() => {
    loadPublicDataRelated();
  }, []);

  useEffect(() => {
    loadAutoCompleteOptions();
  }, [publicDataSourceList, importedDataSourceList]);

  useEffect(() => {
    filterDataList();
  }, [searchKey, publicDataSourceList, importedDataSourceList]);

  const onDragStart = (evt: any, id: string) => {
    evt.dataTransfer.setData('node-type', NodeType.DATA_NODE);
    evt.dataTransfer.setData('data-id', id);
    evt.dataTransfer.setData('label', evt.target.innerText);
    evt.dataTransfer.effectAllowed = 'move';
  };

  const openImportDataDialog = () => {
    if (analysisId === null) {
      throw Error('analysisId is undefined');
    }
    openImportDataUI(analysisId);
  };

  const openUploadDataDialog = () => {
    if (analysisId === null) {
      throw Error('analysisId is undefined');
    }
    openUploadDataUI(analysisId);
  };

  const onSelect = (key: string) => {
    setSearchKey(key);
  };

  const onSearch = (searchText: string) => {
    if (!searchText) {
      setSearchKey('');
    }
    setAutoCompleteOptions(wholeAutoCompleteOptions.filter((item) => item.includes(searchText)));
  };

  const onOpenChange = (openKeys: string[]) => {
    setMenuOpenKeys(openKeys);
  };

  return (
    <div style={{ height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'start', padding: '0.5em 1em 0.5em 1.5em' }}>
        <Button size="small" onClick={() => setDataCaptureModalVisible(true)}>
          <CustomImage
            name={customIconNames.AIICONSTAR}
            style={{ height: '15px', marginRight: '5px', cursor: 'pointer' }}
          />
          <span className="gradient-text">{dictionary.DATA_CAPTURE}</span>
        </Button>
      </div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '0 1em 0 1.5em',
          gap: '1em',
        }}
      >
        <AutoComplete
          options={autoCompleteOptions.map((item) => {
            return { value: item, label: item };
          })}
          style={{ flex: 1 }}
          onSelect={onSelect}
          onSearch={onSearch}
          placeholder={dictionary.SEARCH}
          allowClear
        />
        <Dropdown
          menu={{
            items: [
              {
                key: ImportSource.DATA_SOURCE,
                label: dictionary.IMPORT_FROM_EXISITING_DATA,
              },
              {
                key: ImportSource.DEVICE,
                label: dictionary.UPLOAD_FROM_DEVICE,
              },
              {
                key: ImportSource.THIRD_PARTY_DATA,
                label: dictionary.IMPORT_FROM_DATA_LAKE,
              },
            ],
            onClick: ({ key }: any) => {
              if (key === ImportSource.DATA_SOURCE) {
                openImportDataDialog();
              } else if (key === ImportSource.DEVICE) {
                openUploadDataDialog();
              } else if (key === ImportSource.THIRD_PARTY_DATA) {
                setThirdPartyDataSourceModalVisible(true);
              }
            },
          }}
          placement="bottomLeft"
          arrow={{ pointAtCenter: true }}
        >
          <Button type="text" icon={<PlusOutlined />} />
        </Dropdown>
      </div>
      <Menu mode="inline" openKeys={menuOpenKeys} onOpenChange={onOpenChange}>
        <Menu.SubMenu
          key="public"
          title={
            <span>
              <span style={{ fontWeight: '600' }}>{dictionary.PUBLIC_DATA_LIST}</span>
            </span>
          }
        >
          {filteredPublicDataSourceList.map((value: any) => {
            return (
              <Menu.Item
                style={{
                  padding: 10,
                  margin: '1vh auto',
                  backgroundColor: DataTool.getDataMenuColor(value.state, value.uploadType),
                  color: '#FFF',
                  cursor: analysisAccessType === AnalysisType.PUBLIC ? 'not-allowed' : 'pointer',
                  textAlign: 'center',
                  width: '70%',
                  height: '4.5vh',
                  lineHeight: '4vh',
                  borderRadius: '8px',
                  // border: '1px solid #333',
                }}
                onDragStart={(e: any) => onDragStart(e, value.id)}
                key={`${value.id}`}
                draggable={analysisAccessType !== AnalysisType.PUBLIC}
                title={value.name}
              >
                {value.name}
              </Menu.Item>
            );
          })}
        </Menu.SubMenu>
        <Menu.SubMenu
          key="imported"
          title={
            <span>
              <span style={{ fontWeight: '600' }}>{dictionary.IMPORTED_DATA_LIST}</span>
            </span>
          }
        >
          {filteredImportedDataSourceList.map((value: any) => {
            return (
              <Menu.Item
                style={{
                  padding: 10,
                  margin: '1vh auto',
                  backgroundColor: DataTool.getDataMenuColor(value.state, value.uploadType),
                  color: '#FFF',
                  cursor: analysisAccessType === AnalysisType.PUBLIC ? 'not-allowed' : 'pointer',
                  textAlign: 'center',
                  width: '70%',
                  height: '4.5vh',
                  lineHeight: '4vh',
                  borderRadius: '8px',
                  // border: '1px solid #333',
                }}
                onDragStart={(e: any) => onDragStart(e, value.id)}
                key={`${value.id}`}
                draggable={analysisAccessType !== AnalysisType.PUBLIC}
                title={value.name}
              >
                <span
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    width: '100%',
                  }}
                >
                  <span
                    style={{
                      flex: 1,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                    title={value.name}
                  >
                    {value.name}
                  </span>
                  <span style={{ display: 'flex', gap: '5px' }}>
                    {(value.state === DataState.UPLOADING ||
                      value.state === DataState.PROCESSING ||
                      value.state === DataState.PREHANDLING) && (
                      <LoadingOutlined style={{ color: '#FFF' }} />
                    )}
                    {value.state === DataState.ERROR && (
                      <>
                        <Button
                          size="small"
                          type="text"
                          icon={<QuestionCircleOutlined style={{ color: '#FFF' }} />}
                          onClick={() => openErrorDataUI(value.id)}
                        />
                      </>
                    )}
                  </span>
                </span>
              </Menu.Item>
            );
          })}
        </Menu.SubMenu>
      </Menu>
    </div>
  );
};

export default DataSource;
