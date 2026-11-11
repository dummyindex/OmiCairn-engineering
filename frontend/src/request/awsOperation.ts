import * as constants from '@/constants/index';
import { request } from 'umi';

// Merge the whole file
const requestMultipartUpload = async (uploadId, objectKey, part) => {
  const result = await request(`${constants.API.baseUrl}sss/multipart-upload/complete`, {
    skipErrorHandler: true,
    method: 'POST',
    data: {
      upload_id: uploadId,
      object_key: objectKey,
      parts: part,
    },
    headers: {
      'Content-Type': 'application/json', // Set the request header to JSON
    },
  });
  return result;
};

export const requestCancelUpload = async (uploadId, objectKey) => {
  const result = await request(`${constants.API.baseUrl}sss/multipart-upload/abort`, {
    skipErrorHandler: true,
    method: 'POST',
    data: {
      upload_id: uploadId,
      object_key: objectKey,
    },
    headers: {
      'Content-Type': 'application/json', // Set the request header to JSON
    },
  });
  return result;
};

export const requestUploadToAWS = async (
  file: File,
  partInfoList,
  totalParts,
  partSize,
  objectKey,
  uploadId,
  progressCallback: (progress: number) => void,
) => {
  const uploadPartResultList: any[] = [];

  // Multipart upload
  for (let i = 0; i < totalParts; i++) {
    const start = i * partSize;
    const end = Math.min(start + partSize, file.size);
    const part = file.slice(start, end);

    // Upload a part using the Fetch API
    const uploadPartUrl = partInfoList[i];

    const uploadPartParams = {
      method: 'PUT',
      body: part,
      headers: {
        'Content-Type': 'application/octet-stream',
      },
    };

    const maxRetry = 100;
    let retry = 0;
    let response: any = null;
    while (retry < maxRetry) {
      try {
        response = await fetch(uploadPartUrl, uploadPartParams);
        if (response.ok) break;
      } catch (error) {
        console.warn(`Upload part ${i + 1} failed on attempt ${retry + 1}:`, error);
      }
      retry += 1;
    }

    if (!response.ok) {
      throw Error(`Error uploading part:`, response.statusText);
    }

    const etag = response.headers.get('ETag');
    uploadPartResultList.push({ PartNumber: i + 1, ETag: etag });

    // Update upload progress
    const progress = ((i + 1) / totalParts) * 100;

    progressCallback(progress);
  }

  // Build the complete-upload request

  // Complete the upload using the Fetch API
  const completeResponse = await requestMultipartUpload(uploadId, objectKey, uploadPartResultList);
  console.log('completeResponse', completeResponse);
};

// Upload

export const uploadFileToAWS = (file, presignedUrl, abortController, progressCallback?) => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.upload.addEventListener(
      'progress',
      (event) => {
        if (event.lengthComputable && progressCallback) {
          const percentLoaded = Math.round((event.loaded / event.total) * 100);
          progressCallback(percentLoaded);
        }
      },
      false,
    );

    xhr.onreadystatechange = () => {
      if (xhr.readyState === 4) {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(xhr.response);
        } else {
          reject(xhr.statusText);
        }
      }
    };

    xhr.open('POST', presignedUrl.url, true);

    // Create a FormData object
    const formData = new FormData();

    // Add the file to FormData

    // Add the fields from presignedUrl to FormData
    Object.entries(presignedUrl.fields).forEach(([key, value]) => {
      formData.append(key, value);
    });
    formData.append('file', file);

    // Send FormData
    xhr.send(formData);
  });
};

export const uploadFileToS3 = async (
  file: File,
  uploadInfo: any,
  progressCallback: (process: number) => void,
) => {
  if (uploadInfo.multipart) {
    await requestUploadToAWS(
      file,
      uploadInfo.partInfoList,
      uploadInfo.part_count,
      uploadInfo.part_size,
      uploadInfo.object_key,
      uploadInfo.uploadId,
      progressCallback,
    );
  } else {
    await uploadFileToAWS(file, uploadInfo.presigned_url, null, progressCallback);
  }
};

export const downloadFile = async (
  downloadUrl: string,
  fileName = '',
): Promise<{ success: boolean; error?: string }> => {
  try {
    // Fetch the file first to check if it exists
    const response = await fetch(downloadUrl);

    if (!response.ok) {
      // Check if it's an S3 error (XML response)
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('xml')) {
        const text = await response.text();
        if (text.includes('<Code>NoSuchKey</Code>')) {
          return {
            success: false,
            error: 'File not found - it may have been deleted or corrupted',
          };
        }
        if (text.includes('<Error>')) {
          return { success: false, error: 'Storage error - unable to access file' };
        }
      }
      return { success: false, error: `Download failed: ${response.statusText}` };
    }

    // Create blob from response and trigger download
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);

    const downloadLink = document.createElement('a');
    downloadLink.href = blobUrl;
    downloadLink.download = fileName || 'downloaded_file.txt';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);

    // Clean up blob URL
    window.URL.revokeObjectURL(blobUrl);

    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: `Download failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
    };
  }
};

// Delete
export const requestDeleteDataComponent = async (dataId, componentType) => {
  const result = await request(`${constants.API.baseUrl}data/remove-component`, {
    skipErrorHandler: true,
    method: 'DELETE',
    params: {
      data_id: dataId,
      component_type: componentType,
    },
  });
  return result;
};

// Edit
export const requestEditFileInAWS = async (dataId, oldComponentType, newComponentType) => {
  const result = await request(`${constants.API.baseUrl}data/edit-component-type`, {
    skipErrorHandler: true,
    method: 'POST',
    data: {
      data_id: dataId,
      old_component_type: oldComponentType,
      new_component_type: newComponentType,
    },
    headers: {
      'Content-Type': 'application/json', // Set the request header to JSON
    },
  });
  return result;
};

// Text upload
export const uploadTextToAWS = async (presignedUrl, textContent) => {
  // Perform the upload with an HTTP request
  // For example, you can use axios or fetch
  // Note: this code is only an example; a real project may need to adapt it to its HTTP client library
  const response = await fetch(presignedUrl, {
    method: 'PUT',
    body: textContent,
    headers: {
      'Content-Type': 'text/plain',
    },
  });

  if (!response.ok) {
    console.error('Error uploading text content:', response.statusText);
  } else {
    console.log('Text content uploaded successfully');
  }
};
