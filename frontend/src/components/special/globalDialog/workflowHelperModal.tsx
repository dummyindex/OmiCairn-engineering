import { useModel, useLocation } from 'umi';
import { Modal, Segmented } from 'antd';
import WorkflowGenerator from './workflowHelper/workflowGenerator';
import PipelineTemplate from './workflowHelper/pipelineTemplate';
import './index.less';
import './segmentedButton.css';
import { useEffect, useState } from 'react';

const WorkflowHelperModal = () => {
  const { open, closeModal } = useModel('workflowHelper');
  const { dictionary } = useModel('localization');
  const location = useLocation();
  const [selectedOption, setSelectedOption] = useState('2');

  useEffect(() => {
    if (open) {
      closeModal();
    }
  }, [location.pathname]);

  const segmentedOptions = [
    // {
    //   label: (
    //     <span style={{ whiteSpace: 'nowrap' }}>
    //       <CustomImage
    //         name={AIICONSTAR}
    //         style={{
    //           height: '16px',
    //           marginBottom: '4px',
    //           marginLeft: '-3px',
    //           marginRight: '5px',
    //         }}
    //       />
    //       <span className="gradient-text">AI pipeline</span>
    //     </span>
    //   ),
    //   value: '1',
    // },
    {
      label: (
        <span style={{ whiteSpace: 'nowrap', marginLeft: '5px' }}>
          {dictionary.PIPELINE_TEMPLATE}
        </span>
      ),
      value: '2',
    },
  ];

  return (
    <Modal
      title={null}
      centered
      open={open}
      onCancel={closeModal}
      footer={null}
      width="60vw"
      destroyOnClose
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          margin: '-0.5em 0 1em 0',
        }}
      >
        <div>
          <Segmented
            className="custom-segmented"
            style={{
              borderRadius: '6px',
              padding: '4px',
              width: '20vw',
            }}
            block
            options={segmentedOptions}
            value={selectedOption}
            onChange={setSelectedOption}
          />
        </div>
      </div>
      {selectedOption === '1' && <WorkflowGenerator />}
      {selectedOption === '2' && <PipelineTemplate />}
    </Modal>
  );
};

export default WorkflowHelperModal;
