import { useModel } from 'umi';
import { Button } from 'antd';
import { VitessceStatus } from '@/interfaces/visualPanel';

const commonStyle = {
  fontSize: '12px',
  marginTop: '3vh',
  width: '40%',
};

const VitessceButton = () => {
  const { dataId, vitessceState, startingPrehandleVitessce, openVitessceDetail } =
    useModel('visualPanelControl');

  if (!dataId) {
    return null;
  }

  if (!vitessceState) {
    return (
      <Button
        type="default"
        style={commonStyle}
        loading={startingPrehandleVitessce}
        onClick={openVitessceDetail}
      >
        Prehandle vSpatial
      </Button>
    );
  }

  const { status } = vitessceState;

  if (status === VitessceStatus.PENDING || status === VitessceStatus.RUNNING) {
    return (
      <Button type="default" style={commonStyle} onClick={openVitessceDetail}>
        vSpatial Prehandling ...
      </Button>
    );
  }

  if (status === VitessceStatus.FAILED) {
    return (
      <Button style={commonStyle} type="default" danger onClick={openVitessceDetail}>
        vSpatial Error
      </Button>
    );
  }

  if (status === VitessceStatus.SUCCESS) {
    return (
      <Button style={commonStyle} type="default" onClick={openVitessceDetail}>
        Visualize in vSpatial
      </Button>
    );
  }
};

export default VitessceButton;
