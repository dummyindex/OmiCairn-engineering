import { useState, useEffect } from 'react';

import { Spin, Button } from 'antd';
import {
  CaretRightFilled,
  DeleteOutlined,
  EditOutlined,
  FileTextOutlined,
  LoadingOutlined,
} from '@ant-design/icons';

import './index.css';
import { useModel } from 'umi';

const ReportListItem = ({ report, selectedKey, onSelect, onEdit, onDelete }) => {
  const [expanded, setExpanded] = useState<boolean>(false);

  const metaDataFileName = 'node_interpretation_and_details.txt';

  const reportSelected = `${report.uuid}/${report.reportName}.txt` === selectedKey;
  const metadataSelected = `${report.uuid}/${metaDataFileName}` === selectedKey;

  useEffect(() => {
    if (reportSelected || metadataSelected) {
      setExpanded(true);
    }
  }, [reportSelected, metadataSelected]);

  const producing = report.status !== 'DONE';

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '0 1em 0 2em',
          margin: '0 1em',
          height: '3.5em',
          cursor: producing ? 'not-allowed' : 'pointer',
          borderRadius: '0.5em',
          fontWeight: '450',
          color: producing ? 'rgba(0,0,0,0.5)' : 'rgba(0,0,0,0.8)',
        }}
        onClick={() => {
          if (producing) {
            return;
          }
          setExpanded(!expanded);
        }}
      >
        <CaretRightFilled
          style={{
            fontSize: '1.2em',
            transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s',
          }}
        />
        <span
          style={{
            marginLeft: '0.5em',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {report.uuid}
        </span>
        {producing && (
          <div
            style={{
              marginLeft: 'auto',
              marginRight: '1em',
              color: 'rgba(0,0,0,0.5)',
            }}
          >
            <LoadingOutlined />
          </div>
        )}
      </div>
      {!producing && expanded && (
        <div
          style={{
            margin: '0 0 0 3em',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '0 1em',
              margin: '0 1em',
              height: '3.5em',
              cursor: 'pointer',
              borderRadius: '0.5em',
              backgroundColor: reportSelected ? 'rgba(100,150,255,0.08)' : 'transparent',
              fontWeight: reportSelected ? '500' : '400',
              gap: '0.5em',
            }}
            onClick={() => {
              onSelect(`${report.uuid}/${report.reportName}.txt`);
            }}
          >
            <FileTextOutlined />
            <span
              style={{
                marginLeft: '0.5em',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {report.reportName}
            </span>
            <div style={{ flex: 1 }} />
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={(e: any) => {
                e.stopPropagation();
                onEdit();
              }}
            />
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={(e: any) => {
                e.stopPropagation();
                onDelete();
              }}
            />
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '0 1em',
              margin: '0 1em',
              height: '3.5em',
              cursor: 'pointer',
              borderRadius: '0.5em',
              backgroundColor: metadataSelected ? 'rgba(100,150,255,0.08)' : 'transparent',
              fontWeight: metadataSelected ? '500' : '400',
              gap: '0.5em',
            }}
            onClick={() => {
              onSelect(`${report.uuid}/${metaDataFileName}`);
            }}
          >
            <FileTextOutlined />
            <span
              style={{
                marginLeft: '0.5em',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {metaDataFileName}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

const ReportList = ({
  reportList,
  selectedKey,
  setSelectedKey,
  loading,
  onItemEdit,
  onItemDelete,
}) => {
  const { dictionary } = useModel('localization');
  return (
    <div
      style={{
        height: '100%',
        overflowY: 'auto',
      }}
    >
      <div
        style={{
          height: '3em',
          lineHeight: '3em',
          paddingLeft: '2em',
          borderBottom: '1px solid #f0f0f0',
          fontWeight: '500',
          fontSize: '1.2em',
        }}
      >
        {dictionary.WORKFLOW_REPORT}
      </div>
      {loading ? (
        <Spin indicator={<LoadingOutlined spin />} tip="Loading...">
          <div
            style={{
              width: '100%',
              height: '10vh',
            }}
          />
        </Spin>
      ) : (
        reportList.map((report: any) => (
          <ReportListItem
            key={report.uuid}
            report={report}
            selectedKey={selectedKey}
            onSelect={setSelectedKey}
            onEdit={() => {
              onItemEdit(report);
            }}
            onDelete={() => {
              onItemDelete(report.uuid);
            }}
          />
        ))
      )}
    </div>
  );
};

export default ReportList;
