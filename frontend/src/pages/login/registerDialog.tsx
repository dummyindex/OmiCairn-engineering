import { Modal } from 'antd';

const RegisterMessage = (props: any) => {
  const { isOpen, setIsOpen } = props;
  const closeDialog = () => {
    setIsOpen(false);
  };

  return (
    <Modal
      style={{ zIndex: '999' }}
      title="Register"
      onCancel={closeDialog}
      open={isOpen}
      onOk={() => {
        setIsOpen(false);
      }}
    >
      Self-service registration is disabled in this deployment. Please ask your administrator to
      create an account for you.
    </Modal>
  );
};

export default RegisterMessage;
