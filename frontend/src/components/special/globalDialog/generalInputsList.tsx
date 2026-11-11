import React from 'react';
import { Modal, message, Button, Empty, Input, Select, Spin } from 'antd';
import { useState, useEffect, useRef, useCallback } from 'react';
import { useModel } from 'umi';
import { requestLatestComputation } from '@/request/computation';
import {
  AimOutlined,
  DownloadOutlined,
  FileOutlined,
  FolderOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { requestCreateNode, requestEditNodeParams, requestNodeInfo } from '@/request/node';
import { NodeType } from '@/constants/node';
import { PresetFBs } from '@/constants/functionBlock';
import { requestCreateEdge } from '@/request/edge';
import { requestDispatchTask } from '@/request/task';
import { debounce } from 'lodash';
import { requestGeneralInputsItemDownloadInfo, requestListGeneralInputs } from '@/request/data';

const { Search } = Input;
const { Option } = Select;

const GeneralInputsList = ({ nodeId, open, onClose }) => {
  const { dictionary } = useModel('localization');
  const [dataId, setDataId] = useState<string | null>(null);
  const [downloadingDict, setDownloadingDict] = useState({});
  const [list, setList] = useState<any[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [nextStartAfter, setNextStartAfter] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [fileTypeFilter, setFileTypeFilter] = useState<string>('');
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const refreshDataId = async () => {
    if (!nodeId) {
      setDataId(null);
      return;
    }
    const node = await requestNodeInfo(nodeId);
    if (node.type === NodeType.DATA_NODE_V2) {
      setDataId(node.dataId);
    } else if (node.type === NodeType.COMPUTATION_NODE_V2) {
      const { data: latestComputation } = await requestLatestComputation(node.id);
      setDataId(latestComputation?.resultDataId || null);
    } else {
      throw new Error('Invalid node type for general inputs list');
    }
  };

  const refreshList = async (append: boolean = false) => {
    if (!dataId || loading) {
      if (!append) {
        setList([]);
      }
      return;
    }

    setLoading(true);
    try {
      const { data: outputsS3Info } = await requestListGeneralInputs(dataId + '', {
        start_after_file_name: append ? nextStartAfter || undefined : undefined,
        search_query: searchQuery || undefined,
        file_type_filter: fileTypeFilter || undefined,
        max_keys: 50,
      });

      const { objects, has_more, next_start_after } = outputsS3Info;

      if (append) {
        setList((prevList) => [...prevList, ...objects]);
      } else {
        setList(objects);
      }

      setHasMore(has_more);
      setNextStartAfter(next_start_after);
    } catch (error) {
      console.error('Failed to load outputs:', error);
      message.error('Failed to load outputs');
    } finally {
      setLoading(false);
    }
  };

  // Debounced search handler
  const debouncedSearch = useCallback(
    debounce((query: string) => {
      setSearchQuery(query);
    }, 500),
    [],
  );

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    debouncedSearch(e.target.value);
  };

  const handleFileTypeChange = (value: string) => {
    setFileTypeFilter(value);
  };

  // Handle scroll event for infinite loading
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current || loading || !hasMore) {
      return;
    }

    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;

    // Load more when user scrolls to within 100px of the bottom
    if (scrollHeight - scrollTop - clientHeight < 100) {
      refreshList(true);
    }
  }, [loading, hasMore, nextStartAfter]);

  const downloadFile = async (key: string) => {
    if (!dataId) {
      message.error('dataId is null');
      return;
    }
    setDownloadingDict({
      ...downloadingDict,
      [key]: true,
    });
    try {
      const { data: url } = await requestGeneralInputsItemDownloadInfo(dataId + '', key);
      const a = document.createElement('a');
      a.href = url;
      a.download = key;
      a.click();
    } catch (e) {
      console.error(e);
      message.error('download failed');
    } finally {
      setDownloadingDict({
        ...downloadingDict,
        [key]: false,
      });
    }
  };

  const launchVisualization = async (key: string) => {
    try {
      const h5ad_key = key.split('/').slice(2).join('/');
      if (!nodeId) {
        message.error('Inspected node id is null');
        return;
      }
      const currentNode = await requestNodeInfo(nodeId);
      if (!currentNode) {
        message.error('Current node not found');
        return;
      }
      const { data: newNode } = await requestCreateNode(
        NodeType.COMPUTATION_NODE_V2,
        currentNode.x + 200,
        currentNode.y,
        currentNode.analysisId,
        null,
        PresetFBs.VISUAL.ID + '',
        `Decompose ${h5ad_key} for Visualization`,
      );
      if (!newNode) {
        message.error('Create new node failed');
        return;
      }
      const params = {
        h5ad_key: h5ad_key,
      };
      const editResponse = await requestEditNodeParams(newNode.id, params);
      if (!editResponse) {
        message.error('Edit node params failed');
        return;
      }
      const newEdge = await requestCreateEdge(currentNode.id, newNode.id, currentNode.analysisId);
      if (!newEdge) {
        message.error('Create edge failed');
        return;
      }
      message.success('Visualization launched');
      const launchComputationResponse = await requestDispatchTask(
        currentNode.analysisId,
        [newNode.id],
        [],
      );
      if (!launchComputationResponse) {
        message.error('Launch computation failed');
        return;
      }
    } catch (e) {
      console.error(e);
      message.error('Launch visualization failed');
    }
  };

  useEffect(() => {
    // Reset and refresh when filters change
    setList([]);
    setNextStartAfter(null);
    setHasMore(false);
    refreshList(false);
  }, [dataId, searchQuery, fileTypeFilter, open]);

  useEffect(() => {
    refreshDataId();
  }, [nodeId]);

  useEffect(() => {
    // Attach scroll listener
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => {
        container.removeEventListener('scroll', handleScroll);
      };
    }
  }, [handleScroll]);

  return (
    <Modal
      width="60vw"
      centered
      title={dictionary.OUTPUTS}
      open={open}
      cancelText={dictionary.CLOSE}
      okButtonProps={{ style: { display: 'none' } }}
      onCancel={() => {
        // Reset state when closing
        setList([]);
        setSearchQuery('');
        setFileTypeFilter('');
        setNextStartAfter(null);
        setHasMore(false);
        onClose();
      }}
    >
      <div style={{ marginBottom: '16px', display: 'flex', gap: '8px' }}>
        <Search
          placeholder="Search files..."
          allowClear
          onChange={handleSearchChange}
          style={{ flex: 1 }}
          prefix={<SearchOutlined />}
        />
        <Select
          placeholder="File Type"
          allowClear
          style={{ width: 150 }}
          onChange={handleFileTypeChange}
          value={fileTypeFilter || undefined}
        >
          <Option value="">All Types</Option>
          <Option value="folder">Folders</Option>
          <Option value="png">PNG Images</Option>
          <Option value="jpg">JPG Images</Option>
          <Option value="pdf">PDF Files</Option>
          <Option value="csv">CSV Files</Option>
          <Option value="h5ad">H5AD Files</Option>
          <Option value="txt">Text Files</Option>
          <Option value="json">JSON Files</Option>
        </Select>
      </div>
      <div
        ref={scrollContainerRef}
        style={{
          height: '50vh',
          overflowY: 'auto',
        }}
      >
        {!loading && !list?.length && (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No outputs"
            style={{
              marginTop: '20vh',
            }}
          />
        )}
        {list.map((item) => {
          return (
            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-start',
                padding: '10px',
                gap: '10px',
                borderBottom: '1px solid #f0f0f0',
              }}
              key={item.object_key}
            >
              {item.mime_type === 'folder' ? <FolderOutlined /> : <FileOutlined />}
              <span
                style={{
                  cursor: 'pointer',
                  fontSize: '0.9em',
                }}
              >
                {item.file_name}
              </span>
              <div
                style={{
                  flex: 1,
                }}
              />
              {item.mime_type !== 'folder' && item.file_name.slice(-5) === '.h5ad' && (
                <Button
                  title="launch visualization"
                  size="small"
                  type="text"
                  icon={<AimOutlined />}
                  loading={downloadingDict[item.object_key]}
                  onClick={() => {
                    launchVisualization(item.object_key);
                  }}
                />
              )}
              {item.mime_type !== 'folder' && (
                <Button
                  title="download file"
                  size="small"
                  type="text"
                  icon={<DownloadOutlined />}
                  loading={downloadingDict[item.object_key]}
                  onClick={() => {
                    downloadFile(item.object_key);
                  }}
                />
              )}
            </div>
          );
        })}
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin />
          </div>
        )}
        {!loading && hasMore && (
          <div style={{ textAlign: 'center', padding: '10px', color: '#999' }}>
            Scroll down to load more...
          </div>
        )}
      </div>
    </Modal>
  );
};

export default GeneralInputsList;
