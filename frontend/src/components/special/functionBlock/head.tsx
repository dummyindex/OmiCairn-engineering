import * as customIconNames from '@/assets/customIconNames';
import CustomImage from '@/components/common/customImage';

export default function ManagementHead() {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <div>
        <CustomImage name={customIconNames.WHITELOGO} style={{ height: '5vh', marginTop: '1vh' }} />
      </div>
    </div>
  );
}
