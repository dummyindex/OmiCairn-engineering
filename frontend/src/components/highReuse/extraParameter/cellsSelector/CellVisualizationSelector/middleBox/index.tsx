import { graphUsedOccasion } from '@/constants/graphUsedOccasion';
import { memo, useRef } from 'react';
import { useModel } from 'umi';
import { EmbeddingD32DScatter } from '../chart/embeddingScatter/d32D';
import Embedding2DOptionsBar from '../chart/embeddingScatter/graphOptionBar/embedding2DOptionsBar';
import AxisButton from './axis';
import ChartOperationModeSelect from './chartOperationMode';
import DimensionSwitch from './dimensionSwitch/index';
import style from './index.less';
import LabelButton from './label';
import LegendButton from './legend';
import MaxiMize from './maxiMize';
import PreviewButton from './preview';
import SaveGraph from './saveGraph';

const MiddleBox = memo(() => {
  const childComponentRef = useRef(null);
  const resultImageRef = useRef(null);

  const handleAccessDivInChild = () => {
    if (childComponentRef.current) {
      const divInChild = childComponentRef.current;
      // The child component's div element is accessible here (provided the child component has set the corresponding ref)
      return divInChild;
    }
  };

  const { activeKey, globalChartOptions, currentOptionsBarExpanded } = useModel('cellSelect');

  const renderChart = () => {
    return (
      <EmbeddingD32DScatter
        domId="custom-embedding"
        childComponentRef={childComponentRef}
        occasion={graphUsedOccasion.MAIN}
      />
    );
  };

  const chartPage = () => {
    return (
      <div
        style={{
          height: '60vh',
          position: 'relative',
          border: '0.5px solid rgba(200,200,200,.4)',
          borderRadius: '5px',
          backgroundColor: 'white',
        }}
        ref={resultImageRef}
      >
        <div
          style={{
            height: '8.6vh',
            width: 'calc(42vw - 40px)',
            marginBottom: '0.4px',
            display: 'flex', // Use flex layout
            paddingTop: 15,
            paddingRight: 7,
          }}
        >
          <div
            style={{
              fontSize: '18px',
              paddingLeft: '10px',
            }}
          >
            Embedding
          </div>
          <div style={{ flex: 1 }} />
          <DimensionSwitch />
          <ChartOperationModeSelect />
          {activeKey.name !== 'embedding' ? (
            <PreviewButton />
          ) : (
            <>
              <AxisButton />
              <LabelButton />
              <LegendButton />
            </>
          )}
          <MaxiMize showRef={resultImageRef.current} />
          <SaveGraph onclick={handleAccessDivInChild} />
        </div>
        <Embedding2DOptionsBar />
        <div
          style={{
            height: 'calc(100% - 13vh)',
            width: `calc(100% - ${currentOptionsBarExpanded ? 40 : 0}px)`,
            backgroundColor: globalChartOptions.bgColor,
          }}
        >
          {renderChart()}
        </div>
      </div>
    );
  };

  return <div className={style.middleBox}>{chartPage()}</div>;
});

export default MiddleBox;
