import React, { useRef } from 'react';
import { InboxOutlined } from '@ant-design/icons';
import styles from './fileInput.less';
import { handleFolderEntry } from '@/util/fileTool';

const tidyUpTransferFiles = async (transferFiles: DataTransferItemList) => {
  const fileMap = {};
  for (let i = 0; i < transferFiles.length; i++) {
    const item = transferFiles[i];
    if (item.webkitGetAsEntry) {
      const entry = item.webkitGetAsEntry();
      if (entry && entry.isDirectory) {
        const fileItem: any = {
          type: 'folder',
          children: null,
        };
        const subFileMap = await handleFolderEntry(entry);
        fileItem.children = subFileMap;
        fileMap[entry.name] = fileItem;
      } else if (entry && item.kind === 'file') {
        const file = item.getAsFile();
        const fileItem: any = {
          type: 'file',
          file: file,
        };
        fileMap[entry.name] = fileItem;
      }
    }
  }
  return fileMap;
};

const tidyUpInputFiles = async (files: FileList) => {
  const fileMap = {};
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const fileItem: any = {
      type: 'file',
      file: file,
    };
    fileMap[file.name] = fileItem;
  }
  console.log('fileMap:', fileMap);
  return fileMap;
};

type Trigger = 'drop' | 'click';

type Props = {
  triggers: Trigger[];
  disabled?: boolean;
  onChange: (files: any) => void;
  innerRender?: () => React.ReactNode;
};

const FileInput = ({ triggers, onChange, innerRender, disabled }: Props) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (disabled || !triggers.includes('drop')) {
      return;
    }
    const itemsOrFiles = e.dataTransfer.items;
    if (itemsOrFiles instanceof DataTransferItemList) {
      const fileMap = await tidyUpTransferFiles(itemsOrFiles);
      onChange(fileMap);
    }
  };

  const handleInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      const fileMap = await tidyUpInputFiles(files);
      onChange(fileMap);
    }
  };

  return (
    <div
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      className={`${styles.fileInput} ${
        disabled ? styles.fileInputDisabled : styles.fileInputEnabled
      }`}
      onClick={() => {
        if (disabled || !triggers.includes('click')) {
          return;
        }
        fileInputRef.current?.click();
      }}
    >
      <input
        ref={fileInputRef}
        onChange={handleInputChange}
        type="file"
        multiple
        style={{ display: 'none' }}
      />
      {innerRender ? (
        innerRender()
      ) : (
        <>
          <InboxOutlined
            style={{
              color: '#40a9ff',
              fontSize: '48px',
            }}
          />
          <p
            style={{
              color: '#000000d9',
              fontSize: '16px',
            }}
          >
            Drag file to this area to upload
          </p>
        </>
      )}
    </div>
  );
};

export default FileInput;
