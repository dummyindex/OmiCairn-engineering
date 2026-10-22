import { API } from '@/constants/index';
import { request } from 'umi';

// functionBlockV1 new API

// Get fb info
export const requestGetFBInformation = async (FunctionBlockId: string | number) => {
  const result = await request(`${API.baseUrl}function-block-v1/get-information`, {
    method: 'GET',
    params: {
      function_block_id: FunctionBlockId,
    },
  });
  return result;
};

// Get fb version info
export const requestGetFBVersionInformation = async (FunctionBlockVersionId: string | number) => {
  const result = await request(`${API.baseUrl}function-block-v1/get-version-information`, {
    method: 'GET',
    params: {
      function_block_version_id: FunctionBlockVersionId,
    },
  });
  return result;
};

// Create fb group
export const requestCreateFBGroup = async (groupName: string) => {
  const result = await request(`${API.baseUrl}function-block-v1/create-group`, {
    method: 'POST',
    params: {
      name: groupName,
    },
  });
  return result;
};

// Get public fbs
export const requestPublicFBGroupList = async () => {
  const result = await request(`${API.baseUrl}function-block-v1/get-public-group-list`, {
    skipErrorHandler: true,
  });
  return result;
};

// Get private fbs
export const requestPrivateFBGroupList = async () => {
  const result = await request(`${API.baseUrl}function-block-v1/get-group-list`, {
    skipErrorHandler: true,
  });
  return result;
};

// Upload private fb: get bucket and key
export const requestUploadFunctionBlockPrivate = async (
  fbName: string,
  fbType: string,
  groupId: string,
  versionName: string,
  fileSize,
) => {
  const formData = new FormData();
  formData.append('fb_name', fbName);
  formData.append('fb_type', fbType);
  formData.append('group_id', groupId);
  formData.append('version_name', versionName);
  formData.append('file_size', fileSize);
  const result = await request(`${API.baseUrl}function-block-v1/create`, {
    method: 'POST',
    data: formData,
  });
  return result;
};

// Validate the fb update form
export const requestValidateUpdateForm = async (functionBlockId: string, versionName: string) => {
  const formData = new FormData();
  formData.append('function_block_id', functionBlockId);
  formData.append('version_name', versionName);
  const result = await request(`${API.baseUrl}function-block-v1/validate-update-form`, {
    method: 'POST',
    data: formData,
  });
  return result;
};

// Preprocess fb version
export const requestPreprocessFunctionBlockVersion = async (functionBlockVersionId: string) => {
  const result = await request(`${API.baseUrl}function-block-v1/preprocess-version`, {
    method: 'POST',
    params: {
      function_block_version_id: functionBlockVersionId,
    },
  });
  return result;
};

// Update fb
export const requestUpdateFunctionBlockPrivate = async (
  functionBlockId: string,
  versionName: string,
  file_size: string | number,
) => {
  const formData = new FormData();
  formData.append('function_block_id', functionBlockId);
  formData.append('version_name', versionName);
  formData.append('file_size', file_size + '');
  const result = await request(`${API.baseUrl}function-block-v1/create-version`, {
    method: 'POST',
    data: formData,
  });
  return result;
};

// Upload private fb to AWS
// Initialize upload
export const initiateUpload = async (s3, bucketName, objectKey) => {
  const params = {
    Bucket: bucketName,
    Key: objectKey,
  };

  try {
    const response = await s3.createMultipartUpload(params).promise();
    return response.UploadId;
  } catch (error) {
    console.error('Error initializing upload:', error);
    throw error;
  }
};

// Merge the whole file
export const requestUploadFBToAWS = async (
  file: File,
  UploadId,
  s3,
  bucketName: string,
  objectkey: string,
  progressCallback: (progress: number) => void,
) => {
  const params = {
    Bucket: bucketName,
    Key: objectkey, // Object name in the bucket
    Body: file, // File to upload
    ContentLength: file.size, // File size
  };

  try {
    // Create the initial upload task
    const partSize = 50 * 1024 * 1024; // Size of each part (bytes)
    const totalParts = Math.ceil(file.size / partSize); // Total number of parts
    const uploadPartsPromises = [];
    const percentageArr: any[] = new Array(totalParts).fill(0);
    const preNumberArr: any[] = new Array(totalParts).fill(0);
    const onPartProgress = (partNumber: number, progress: number) => {
      if (percentageArr[partNumber - 1] < progress) {
        percentageArr[partNumber - 1] = progress;
        if (percentageArr[partNumber - 1] > preNumberArr[partNumber - 1]) {
          preNumberArr[partNumber - 1] = percentageArr[partNumber - 1];
        }
        const totalProgress = preNumberArr.reduce((total, value) => {
          return total + value;
        }, 0);
        progressCallback(totalProgress / file.size);
      }
    };

    // Multipart upload
    for (let i: number = 0; i < totalParts; i++) {
      const start = i * partSize;
      const end = Math.min(start + partSize, file.size);
      const partParams = {
        ...params,
        PartNumber: i + 1,
        UploadId,
        Body: file.slice(start, end),
      };

      const uploadPartPromise = s3
        .uploadPart(partParams)
        .on('httpUploadProgress', function (evt) {
          // console.log(evt);
          // console.log(i + 1, 'Part Uploaded:', evt.loaded, '/', partSize);
          onPartProgress(i + 1, evt.loaded);
          // progressCallback(evt.loaded/partSize,percentageArr,partNumber)
        })
        .promise();
      uploadPartsPromises.push(uploadPartPromise);
    }

    // Wait for all parts to finish uploading
    const uploadedParts = await Promise.all(uploadPartsPromises);

    const completeParams = {
      Bucket: bucketName,
      Key: objectkey,
      MultipartUpload: {
        Parts: uploadedParts.map((part, index) => ({ ETag: part.ETag, PartNumber: index + 1 })),
      },
      UploadId,
    };

    // Merge parts
    const result = await s3.completeMultipartUpload(completeParams).promise();

    // Post-upload handling
    console.log('File uploaded successfully!');
    return result;
  } catch (error) {
    // Handle errors
    console.log('File upload failed:', error);
  }
};

// Upload fb validation
export const requestValidateUpdate = async (
  fbName: string,
  fbType: string,
  groupId: string,
  versionName: string,
) => {
  const formData = new FormData();
  formData.append('fb_name', fbName);
  formData.append('fb_type', fbType);
  formData.append('group_id', groupId);
  formData.append('version_name', versionName);
  const result = await request(`${API.baseUrl}function-block-v1/validate-creation-form`, {
    skipErrorHandler: true,
    method: 'POST',
    data: formData,
  });
  return result;
};

// Search fbs
export const requestSearchFunctionBlockMenuList = async (data: string) => {
  const result = await request(`${API.baseUrl}function-block-v1/search`, {
    method: 'POST',
    params: {
      search_key: data,
    },
  });
  return result;
};

// Get fb preview image list
export const requestGetFBPreviewList = async (params: {
  functionBlockId: string | null;
  functionBlockVersionId: string | null;
}) => {
  const { functionBlockId, functionBlockVersionId } = params;
  const result = await request(`${API.baseUrl}function-block-v1/get-preview-images-list`, {
    method: 'GET',
    params: {
      function_block_id: functionBlockId,
      function_block_version_id: functionBlockVersionId,
    },
  });
  return result;
};

// Get fb version list
export const requestGetFBVersionList = async (functionBlockId: string | number) => {
  const result = await request(`${API.baseUrl}function-block-v1/get-version-list`, {
    method: 'GET',
    params: {
      function_block_id: functionBlockId,
    },
  });
  return result;
};

// Switch fb version
export const requestSwitchFunctionBlockVersion = async (
  functionBlockId: string | number,
  versionId: string | number,
) => {
  const result = await request(`${API.baseUrl}function-block-v1/switch-version`, {
    method: 'POST',
    params: {
      function_block_id: functionBlockId,
      version_id: versionId,
    },
  });
  return result;
};

// Get updated fb list
export const requestUpdatedRecords = async (startTime: string) => {
  const result = await request(`${API.baseUrl}function-block-v1/get-updated-records`, {
    method: 'GET',
    params: {
      start_time: startTime,
    },
  });
  return result;
};

// Get mini app fb list
export const requestMiniAppFBList = async (
  offset: number,
  limit: number,
  searchKey: string | null = null,
) => {
  const result = await request(`${API.baseUrl}function-block-v1/get-mini-tool-list`, {
    method: 'GET',
    params: {
      offset,
      limit,
      search_key: searchKey,
    },
  });
  return result;
};

// Get favorited fb list
export const requestCollectedMiniAppList = async (
  offset: number,
  limit: number,
  searchKey: string,
) => {
  const result = await request(`${API.baseUrl}function-block-v1/get-collected-mini-tool-list`, {
    method: 'GET',
    params: {
      offset,
      limit,
      search_key: searchKey,
    },
  });
  return result;
};

// Check favorite status by ids
export const requestCheckCollected = async (ids: string[]) => {
  const result = await request(`${API.baseUrl}function-block-v1/check-collected`, {
    method: 'POST',
    data: {
      function_block_ids: ids,
    },
  });
  return result;
};

// Favorite a function block
export const requestCollectFunctionBlock = async (functionBlockId: string) => {
  const result = await request(`${API.baseUrl}function-block-v1/collect`, {
    method: 'POST',
    params: {
      function_block_id: functionBlockId,
    },
  });
  return result;
};

// Unfavorite a function block
export const requestCancelCollectFunctionBlock = async (functionBlockId: string) => {
  const result = await request(`${API.baseUrl}function-block-v1/cancel-collect`, {
    method: 'POST',
    params: {
      function_block_id: functionBlockId,
    },
  });
  return result;
};

export const requestFBVersionContent = async (functionBlockVersionId: string, fileName: string) => {
  const result = await request(`${API.baseUrl}function-block-v1/get-version-content`, {
    method: 'GET',
    params: {
      function_block_version_id: functionBlockVersionId,
      file: fileName,
    },
  });
  return result;
};

export const requestDataCapture = async (userRequest: string) => {
  const result = await request(`${API.baseUrl}gpt/capture-data`, {
    method: 'GET',
    params: {
      user_request: userRequest,
    },
  });
  return result;
};

export const requestFBVersionStructure = async (functionBlockVersionId: string) => {
  const result = await request(`${API.baseUrl}function-block-v1/get-version-structure`, {
    method: 'GET',
    params: {
      function_block_version_id: functionBlockVersionId,
    },
  });
  return result;
};

export const requestFBVersionDownload = async (functionBlockVersionId: string) => {
  const result = await request(`${API.baseUrl}function-block-v1/download-version`, {
    method: 'GET',
    params: {
      function_block_version_id: functionBlockVersionId,
    },
  });
  return result;
};
