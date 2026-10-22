import type { UploadFile } from 'antd/es/upload/interface';

/**
 * Props type for the ExtraFilesDialog component
 */
export interface ExtraFilesDialogProps {
  /** Whether the dialog is visible */
  visible: boolean;

  /** Node ID, used to load existing files */
  nodeId: string;

  /** Callback invoked when the Cancel button is clicked */
  onCancel: () => void;

  /** Callback invoked when the OK button is clicked; receives the list of successfully uploaded files */
  onOk?: (files: UploadFile[]) => void;

  /** Dialog title */
  title?: string;

  /** Maximum file size limit (in MB) */
  maxFileSize?: number;
}

/**
 * Extended upload file type that includes upload information
 */
export interface ExtendedUploadFile extends UploadFile {
  /** Information returned by the S3 upload */
  uploadInfo?: {
    presigned_url?: string;
    object_key?: string;
    multipart?: boolean;
    part_count?: number;
    part_size?: number;
    uploadId?: string;
    partInfoList?: any[];
  };
}

/**
 * File upload status
 */
export type FileUploadStatus = 'uploading' | 'done' | 'error' | 'removed';

/**
 * File statistics
 */
export interface FileStats {
  /** Total number of files */
  total: number;

  /** Number of successful uploads */
  success: number;

  /** Number of uploads in progress */
  uploading: number;

  /** Number of failed uploads */
  failed: number;
}
