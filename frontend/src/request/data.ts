import * as constants from '@/constants/index';
import { request } from 'umi';

// Change to dataUrl later
export const requestDownloadDataSource = async (dataId: string) => {
  const result = await request(`${constants.API.baseUrl}data/download/info/get`, {
    skipErrorHandler: true,
    method: 'GET',
    params: {
      data_id: dataId,
    },
  });
  return result;
};

export const requestDataSourceList = async (
  mode: string,
  analysisId: string | null = null,
  searchKey: string | null = null,
) => {
  const params: any = {
    mode,
    analysis_id: analysisId,
  };

  if (searchKey && searchKey.trim() !== '') {
    params.search_key = searchKey;
  }

  const result = await request(`${constants.API.baseUrl}data/list/get`, {
    skipErrorHandler: true,
    method: 'GET',
    params,
  });
  return result;
};

export const requestDeleteDataSource = async (dataSourceId: string) => {
  const result = await request(`${constants.API.baseUrl}data/remove`, {
    skipErrorHandler: true,
    method: 'DELETE',
    params: {
      data_id: dataSourceId,
    },
  });
  return result;
};

export const requestSpeciesList = async () => {
  const result = await request(`${constants.API.baseUrl}data/species/list/get`, {
    skipErrorHandler: true,
    method: 'GET',
  });
  return result;
};

// Change to dataUrl later
export const requestCreateDataFrame = async (
  dataFrom,
  name: string | null = null,
  uploadType: string,
  species: string,
  description: string,
) => {
  const formData = new FormData();
  formData.append('data_from', dataFrom);
  formData.append('upload_type', uploadType);
  formData.append('species', species);
  formData.append('description', description);
  if (name) {
    formData.append('name', name);
  }
  const result = await request(`${constants.API.baseUrl}data/framework/create`, {
    skipErrorHandler: true,
    method: 'POST',
    data: formData,
  });
  return result;
};

// Change to dataUrl later  ?
export const requestAnndataUploadInfo = async (dataFrameId: string, fileSize) => {
  const result = await request(`${constants.API.baseUrl}data/upload/info/get`, {
    skipErrorHandler: true,
    method: 'GET',
    params: {
      data_id: dataFrameId,
      file_size: fileSize,
    },
  });
  return result;
};

// Abort the AWS upload
export const cancelUploadS3Part = (s3, bucketName: string, objectkey: string, uploadId: string) => {
  return new Promise((resolve) => {
    s3.abortMultipartUpload(
      {
        Bucket: bucketName,
        Key: objectkey,
        UploadId: uploadId,
      },
      (err, data) => {
        if (err) {
          console.error(err);
        } else {
          console.log(data);
          resolve(data);
        }
      },
    );
  });
};

// Change to dataUrl later
export const requestCheckAnndataUpload = async (dataFrameId: string) => {
  const result = await request(`${constants.API.dataUrl}/pretreatment/confirm-whole-adata-upload`, {
    skipErrorHandler: true,
    method: 'GET',
    timeout: 1000 * 60 * 10,
    params: {
      data_id: dataFrameId,
    },
  });
  return result;
};

// Request upload component; returns bucket name and key
export const requestDataComponentUploadInfo = async (
  dataFrameId: string,
  componentType: string,
  fileSuffix: string,
  uploadType: string,
  fileSize,
) => {
  const result = await request(`${constants.API.baseUrl}data/component/upload/info/get`, {
    skipErrorHandler: true,
    method: 'GET',
    params: {
      data_id: dataFrameId,
      component_type: componentType,
      file_suffix: fileSuffix,
      upload_type: uploadType,
      file_size: fileSize,
    },
  });
  return result;
};

// Changed to dataUrl
export const requestAssembleDataComponent = async (dataFrameId: string) => {
  const result = await request(
    `${constants.API.dataUrl}/pretreatment/confirm-data-components-upload`,
    {
      skipErrorHandler: true,
      method: 'GET',
      params: {
        data_id: dataFrameId,
      },
    },
  );
  return result;
};

export const requestVitessceState = async (data_id: string | number) => {
  const { data: response } = await request(
    `${constants.API.dataUrl}/pretreatment/get-vitessce-state`,
    {
      method: 'GET',
      params: {
        data_id: data_id,
      },
    },
  );
  if (response && response.options) {
    response.options = JSON.parse(response.options);
  }
  return response;
};

export const requestStartVitesscePrehandle = async (
  data_id: string | number,
  node_id: string | number,
  options: any,
) => {
  const { data: response } = await request(
    `${constants.API.dataUrl}/pretreatment/start-vitessce-prehandle`,
    {
      method: 'POST',
      data: {
        data_id: data_id,
        node_id: node_id,
        options: JSON.stringify(options),
      },
    },
  );
  if (response && response.options) {
    response.options = JSON.parse(response.options);
  }
  return response;
};

export const requestDataCollect = async (nodeId: string, name: string) => {
  const result = await request(`${constants.API.baseUrl}data/collect`, {
    skipErrorHandler: true,
    method: 'GET',
    params: {
      node_id: nodeId,
      data_name: name,
    },
  });
  return result;
};

// Edit imported data
export const requestDataEdit = async (dataId: string, name: string, description: string) => {
  const result = await request(`${constants.API.baseUrl}data/edit`, {
    skipErrorHandler: true,
    method: 'POST',
    data: {
      data_id: dataId,
      name: name,
      description: description,
    },
  });
  return result;
};

// Upload next-step validation API
export const requestValidateUpdate = async (species: string, description: string) => {
  const formData = new FormData();
  formData.append('species', species);
  formData.append('description', description);
  const result = await request(`${constants.API.baseUrl}/data/validate-creation-form`, {
    skipErrorHandler: true,
    method: 'POST',
    data: formData,
  });
  return result;
};

export const requestPageThirdPartyDataList = async (
  page: number,
  pageSize: number,
  searchKey: string,
) => {
  const result = await request(`${constants.API.baseUrl}data/page-3-part-data-source`, {
    method: 'GET',
    params: {
      page,
      page_size: pageSize,
      search: !!searchKey ? searchKey : undefined,
    },
  });
  return result;
};

export const requestDataInfo = async (dataId: string) => {
  const result = await request(`${constants.API.baseUrl}data/get-data-info`, {
    skipErrorHandler: true,
    method: 'GET',
    params: {
      data_id: dataId,
    },
  });
  return result;
};

export const requestDataReferencedState = async (dataId: string) => {
  const result = await request(`${constants.API.baseUrl}data/get-referenced-state`, {
    skipErrorHandler: true,
    method: 'GET',
    params: {
      data_id: dataId,
    },
  });
  return result;
};

export const requestListGeneralInputs = async (
  dataId: string,
  options?: {
    prefix?: string;
    start_after_file_name?: string;
    max_keys?: number;
    search_query?: string;
    file_type_filter?: string;
  },
) => {
  const res = await request(`${constants.API.baseUrl}data/list-general-inputs`, {
    method: 'GET',
    params: {
      data_id: dataId,
      prefix: options?.prefix,
      start_after_file_name: options?.start_after_file_name,
      max_keys: options?.max_keys || 50,
      search_query: options?.search_query,
      file_type_filter: options?.file_type_filter,
    },
  });
  return res;
};

export const requestGeneralInputsItemDownloadInfo = async (dataId: string, key: string) => {
  const res = await request(`${constants.API.baseUrl}data/get-general-input-item-download-info`, {
    method: 'GET',
    params: {
      data_id: dataId,
      object_key: key,
    },
  });
  return res;
};
