import { requestFBVersionContent, requestGetFBVersionInformation } from '@/request/functionBlock';
import { writeToClipboard } from '@/util/operationTools';
import { CopyOutlined } from '@ant-design/icons';
import Editor from '@monaco-editor/react';
import { Button, message, Modal } from 'antd';
import { useEffect, useState } from 'react';
import { useModel } from 'umi';
import './index.less';

const CodeModal = () => {
  const { fbVersionId, setFbVersionId } = useModel('visualPanelControl');
  const [codeContent, setCodeContent] = useState<string>('');
  const [requirementsContent, setRequirementsContent] = useState<string>('');
  const [staticConfigContent, setStaticConfigContent] = useState<string>('');
  const [installScript, setInstallScript] = useState<string>('');
  const [codeLanguage, setCodeLanguage] = useState<string[]>(['python', 'json', 'text']);

  const [modalWidth, setModalWidth] = useState(window.innerWidth * 0.8);
  const [modalHeight, setModalHeight] = useState(window.innerHeight * 0.85);

  const maxModalWidth = window.innerWidth * 0.91;
  const maxModalHeight = window.innerHeight * 0.91;

  const handleResizeStart = (e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = modalWidth;
    const startHeight = modalHeight;

    const handleResize = (moveEvent: MouseEvent) => {
      const newWidth = Math.min(
        maxModalWidth,
        Math.max(800, startWidth + moveEvent.clientX - startX),
      );
      const newHeight = Math.min(
        maxModalHeight,
        Math.max(600, startHeight + moveEvent.clientY - startY),
      );
      setModalWidth(newWidth);
      setModalHeight(newHeight);
    };

    const handleResizeStop = () => {
      document.removeEventListener('mousemove', handleResize);
      document.removeEventListener('mouseup', handleResizeStop);
    };

    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', handleResizeStop);
  };

  const handleCloseCodeModal = () => {
    setFbVersionId('');
    setCodeContent('');
    setRequirementsContent('');
    setStaticConfigContent('');
    setInstallScript('');
  };

  const handleOpenCodeModal = async () => {
    if (!fbVersionId) return;
    try {
      const { data: fbVersion } = await requestGetFBVersionInformation(fbVersionId);
      let fileList: string[] | null = null;
      const codeLanguage = fbVersion?.programLanguage?.toLowerCase() || 'Unknown';
      const isV2 = fbVersion?.isV2 || false;
      if (!isV2) {
        if (codeLanguage === 'python') {
          setCodeLanguage(['python', 'json', 'text', 'shell']);
          fileList = ['function_block.py', 'static-config.json', 'requirements.txt', 'install.sh'];
        } else if (codeLanguage === 'r') {
          setCodeLanguage(['r', 'json', 'r', 'shell']);
          fileList = ['function_block.R', 'static-config.json', 'libs.R', 'install.sh'];
        } else if (codeLanguage === 'bash') {
          setCodeLanguage(['bash', 'json', 'bash', 'shell']);
          fileList = ['function_block.sh', 'static-config.json', 'libs.sh', 'install.sh'];
        } else {
          throw new Error('Unsupported language type');
        }
      } else {
        setCodeLanguage(['shell', 'json', 'text', 'text']);
        fileList = ['run.sh', 'static-config.json', null, null];
      }
      const requestContent = async (fileName: string) => {
        if (!fileName) return '';
        const { data } = await requestFBVersionContent(fbVersionId, fileName);
        return data || '';
      };
      const [code, staticConfig, requirements, installScript] = await Promise.all(
        fileList.map(requestContent),
      );
      setCodeContent(code);
      setStaticConfigContent(staticConfig);
      setInstallScript(installScript);
      setRequirementsContent(requirements);
    } catch (error) {
      console.error('Error loading code content:', error);
      message.error('Failed to load code content');
      handleCloseCodeModal();
    }
  };

  const handleCopyCode = (content: string) => {
    try {
      writeToClipboard(content);
      message.success('Code copied to clipboard!');
    } catch (error) {
      message.error('Failed to copy code.');
      console.error('Copy failed:', error);
    }
  };

  useEffect(() => {
    if (fbVersionId) {
      const modalRoot = document.querySelector('.ant-modal-root');
      if (modalRoot) {
        const parent = modalRoot.parentNode;
        if (parent) {
          parent.removeChild(modalRoot);
          parent.appendChild(modalRoot);
        }
      }
      handleOpenCodeModal();
    }
  }, [fbVersionId]);

  const mainEditorHeight = Math.floor((modalHeight - 120) * 0.5);
  const subEditorHeight = Math.floor((modalHeight - 120) * 0.6) - 50;

  return (
    <Modal
      centered
      title="Node Code"
      open={!!fbVersionId}
      onCancel={handleCloseCodeModal}
      footer={null}
      width={modalWidth}
      bodyStyle={{
        padding: 0,
        height: modalHeight - 60,
        overflowY: 'auto',
        position: 'relative',
        top: '10px',
        left: '10px',
      }}
      style={{
        resize: 'both',
        overflow: 'hidden',
        position: 'relative',
      }}
      getContainer={() => document.body}
    >
      <div style={{ height: '100%', position: 'relative' }}>
        <div style={{ position: 'relative' }}>
          <div style={{ padding: '10px 0 0 10px', fontWeight: 'bold' }}>Core Code:</div>
          <Button
            icon={<CopyOutlined />}
            onClick={() => handleCopyCode(codeContent)}
            type="text"
            size="large"
            style={{
              marginRight: 10,
              color: 'white',
              position: 'absolute',
              top: 30,
              right: 10,
              zIndex: 1,
            }}
          />
          <Editor
            height={`${mainEditorHeight}px`}
            language={codeLanguage[0]}
            theme="vs-dark"
            value={codeContent}
            options={{
              fontSize: 14,
              readOnly: true,
              minimap: { enabled: false },
              automaticLayout: true,
              padding: { top: 10 },
            }}
          />
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-start',
            alignItems: 'stretch',
            width: '100%',
            gap: '20px',
            height: `${subEditorHeight}px`,
          }}
        >
          <div style={{ position: 'relative', flex: '1' }}>
            <div style={{ padding: '10px 0 0 10px', fontWeight: 'bold' }}>Static Configure:</div>
            <Button
              icon={<CopyOutlined />}
              onClick={() => handleCopyCode(staticConfigContent)}
              type="text"
              size="large"
              style={{
                marginRight: 10,
                color: 'white',
                position: 'absolute',
                top: 30,
                right: 10,
                zIndex: 1,
              }}
            />
            <Editor
              language={codeLanguage[1]}
              theme="vs-dark"
              height={subEditorHeight - 40}
              value={staticConfigContent}
              options={{
                fontSize: 14,
                readOnly: true,
                minimap: { enabled: false },
                automaticLayout: true,
                padding: { top: 10 },
              }}
            />
          </div>
          <div style={{ position: 'relative', flex: '1' }}>
            <div style={{ padding: '10px 0 0 10px', fontWeight: 'bold' }}>Requirements:</div>
            <Button
              icon={<CopyOutlined />}
              onClick={() => handleCopyCode(requirementsContent)}
              type="text"
              size="large"
              style={{
                marginRight: 10,
                color: 'white',
                position: 'absolute',
                top: 30,
                right: 10,
                zIndex: 1,
              }}
            />
            <Editor
              language={codeLanguage[2]}
              theme="vs-dark"
              height={subEditorHeight - 40}
              value={requirementsContent}
              options={{
                fontSize: 14,
                readOnly: true,
                minimap: { enabled: false },
                automaticLayout: true,
                padding: { top: 10 },
              }}
            />
          </div>
          <div style={{ position: 'relative', flex: '1' }}>
            <div style={{ padding: '10px 0 0 10px', fontWeight: 'bold' }}>Install Script:</div>

            <Button
              icon={<CopyOutlined />}
              onClick={() => handleCopyCode(installScript)}
              type="text"
              size="large"
              style={{
                marginRight: 10,
                color: 'white',
                position: 'absolute',
                top: 30,
                right: 10,
                zIndex: 1,
              }}
            />
            <Editor
              language={codeLanguage[3]}
              theme="vs-dark"
              height={subEditorHeight - 40}
              value={installScript}
              options={{
                fontSize: 14,
                readOnly: true,
                minimap: { enabled: false },
                automaticLayout: true,
                padding: { top: 10 },
              }}
            />
          </div>
        </div>
        <div
          style={{
            position: 'absolute',
            width: '20px',
            height: '20px',
            right: 0,
            bottom: 0,
            cursor: 'se-resize',
            backgroundColor: 'transparent',
            zIndex: 1000,
          }}
          onMouseDown={handleResizeStart}
        />
      </div>
    </Modal>
  );
};

export default CodeModal;
