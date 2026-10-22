import { Divider } from 'antd';
import CategoryBox from './obs/categoryBox';
import ContinueBox from './obs/continueBox';

const ObsContent = (props) => {
  const { dataStructure } = props;
  const obs = dataStructure?.obs || [];

  const { categoryKeys, continuousKeys } = obs.reduce(
    (acc: any, cur: any) => {
      if (cur.dtype === 'category' || cur.dtype === 'bool') {
        acc.categoryKeys.push(cur.key);
      } else if (cur.dtype.startsWith('float')) {
        acc.continuousKeys.push(cur.key);
      }
      return acc;
    },
    { categoryKeys: [], continuousKeys: [] },
  );
  // console.log('continuousKeys', continuousKeys);
  // console.log('dataStructureClassification', dataStructureClassification);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: '98%',
        height: '100%',
      }}
    >
      <CategoryBox categoryKeys={categoryKeys} />
      <Divider />
      <ContinueBox continuousKeys={continuousKeys} />
    </div>
  );
};

export default ObsContent;
