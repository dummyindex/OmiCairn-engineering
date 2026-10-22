import { Modal } from 'antd';

const { confirm } = Modal;

const promiseConfirm = (options: any) => {
  return new Promise((resolve) => {
    confirm({
      ...options,
      onOk() {
        resolve(true);
      },
      onCancel() {
        resolve(false);
      },
    });
  });
};

export default promiseConfirm;
