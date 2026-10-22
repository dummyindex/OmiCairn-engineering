import type { FileMap } from '@/interfaces/file';

export const readFolderEntry = (entry: any) => {
  return new Promise((resolve, reject) => {
    const reader = entry.createReader();
    reader.readEntries((entries: any) => {
      resolve(entries);
    }, reject);
  });
};

export const getFileBlob = async (fileEntry: FileSystemFileEntry): Promise<Blob> => {
  return new Promise((resolve, reject) => {
    fileEntry.file((file) => {
      resolve(file);
    }, reject);
  });
};

export const handleFolderEntry = async (entry: any) => {
  console.time('handleFolderEntry');
  const fileMap = {};
  const entries = await readFolderEntry(entry);
  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];
    if (entry.isDirectory) {
      const fileItem: any = {
        type: 'folder',
        children: null,
      };
      const subFileMap = await handleFolderEntry(entry);
      fileItem.children = subFileMap;
      fileMap[entry.name] = fileItem;
    } else {
      const file = await getFileBlob(entry);
      const fileItem: any = {
        type: 'file',
        file: file,
      };
      fileMap[entry.name] = fileItem;
    }
  }
  console.timeEnd('handleFolderEntry');
  return fileMap;
};

export const abstractFileNameList = (fileMap: FileMap) => {
  const result: string[] = [];
  const keys = Object.keys(fileMap);
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    const fileItem = fileMap[key];
    if (fileItem.type === 'file') {
      result.push(key);
    } else if (fileItem.type === 'folder') {
      const children = fileItem.children;
      if (children) {
        const subFileNames = abstractFileNameList(children);
        result.push(...subFileNames.map((name) => `${key}/${name}`));
      }
    }
  }
  return result;
};

export const flatFileMap = (fileMap: FileMap) => {
  const result: FileMap = {};
  const keys = Object.keys(fileMap);
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    const fileItem = fileMap[key];
    result[key] = fileItem;
    if (fileItem.type === 'folder') {
      const children = fileItem.children;
      if (children) {
        const subFileMap = flatFileMap(children);
        Object.keys(subFileMap).forEach((subKey) => {
          result[`${key}/${subKey}`] = subFileMap[subKey];
        });
      }
    }
  }
  return result;
};

export const getInferiorFileMap = (fileMap: FileMap, path: string[]) => {
  let currentFileMap: FileMap | null = fileMap;
  for (let i = 0; i < path.length; i++) {
    const key = path[i];
    const fileItem = currentFileMap?.[key];
    if (!fileItem) {
      return null;
    }
    if (fileItem.type === 'folder' && i < path.length - 1) {
      currentFileMap = fileItem.children;
    }
  }
  return currentFileMap;
};

export const formatFileSize = (size: number) => {
  if (size < 1024) {
    return `${size} B`;
  } else if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(2)} KB`;
  } else if (size < 1024 * 1024 * 1024) {
    return `${(size / 1024 / 1024).toFixed(2)} MB`;
  } else {
    return `${(size / 1024 / 1024 / 1024).toFixed(2)} GB`;
  }
};
