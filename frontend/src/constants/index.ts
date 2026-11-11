// Backend base URL. Configure with UMI_APP_API_URL_PREFIX (see .env.example);
// defaults to a backend running locally.
const urlPrefix = process.env.UMI_APP_API_URL_PREFIX || 'http://localhost:8099/';

export const API = {
  baseUrl: `${urlPrefix}server/`,
  dataUrl: `${urlPrefix}data/`,
  computationServerUrl: `${urlPrefix}computation-server/`,
};

// Object-storage backend used for presigned uploads/downloads (S3-compatible).
export const ServiceCloud = process.env.UMI_APP_SERVICE_CLOUD || 'AWS';

// Base URL for static UI images (logos, icons). Defaults to ./public/static.
export const StaticResourceBaseUrl = process.env.UMI_APP_STATIC_RESOURCE_BASE_URL || '/static';

// Optional download link for the example function-block package; the button is hidden when unset.
export const DemoFunctionBlockUrl = process.env.UMI_APP_DEMO_FUNCTION_BLOCK_URL || '';

export const SpaceType = {
  DATASPACE: 'data-space',
  ANALYSISSPACE: 'analysis-space',
};

export const Version = 'V12.3.66';

export const VersionUpdatedTime = '2026-02-09';
export const IdentityStatus = {
  OWNER: 'owner',
  GUEST: 'guest',
};
