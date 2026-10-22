import { ArrowsAltOutlined, ShrinkOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useModel } from 'umi';

const MaxiMize = (props: any) => {
  // const [isFillScreen, setIsFillScreen] = useState(false);
  const { isFillScreen, setIsFillScreen } = useModel('cellSelect');
  const { showRef } = props;

  const enterFullScreen = () => {
    if (!showRef) {
      return;
    }
    if (showRef.requestFullscreen) {
      showRef.requestFullscreen();
    } else if (showRef.webkitRequestFullscreen) {
      showRef.webkitRequestFullscreen();
    } else if (showRef.mozRequestFullScreen) {
      showRef.mozRequestFullScreen();
    } else if (showRef.msRequestFullscreen) {
      showRef.msRequestFullscreen();
    }
  };

  const exitFullScreen = () => {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if ((document as any).webkitExitFullscreen) {
      (document as any).webkitExitFullscreen();
    } else if ((document as any).mozCancelFullScreen) {
      (document as any).mozCancelFullScreen();
    } else if ((document as any).msExitFullscreen) {
      (document as any).msExitFullscreen();
    }
  };

  document.addEventListener('fullscreenchange', function () {
    if (document.fullscreenElement) {
      setIsFillScreen(true);
    } else if (!document.fullscreenElement) {
      // Code to run when exiting fullscreen
      // Update the display state
      setIsFillScreen(false);
    }
  });

  return (
    <div
      style={{
        marginLeft: '0.2vw',
        marginRight: '0.2vw',
        // position: 'absolute',
        // zIndex: '9999',
        // top: '15px',
        // right: galleryMode ? '65px' : '165px',
      }}
    >
      {!isFillScreen ? (
        <Button onClick={enterFullScreen} icon={<ArrowsAltOutlined style={{ color: '#888' }} />} />
      ) : (
        <Button onClick={exitFullScreen} icon={<ShrinkOutlined style={{ color: '#888' }} />} />
      )}
    </div>
  );
};

export default MaxiMize;
