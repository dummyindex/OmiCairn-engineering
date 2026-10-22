import { CloseOutlined, FullscreenExitOutlined, FullscreenOutlined } from '@ant-design/icons';
import { Button } from 'antd';

const PreviousParameter = ({ previousParamDict, onClose, maximized, setMaximized }) => {
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        backgroundColor: 'white',
        borderRadius: '10px',
        overflowY: 'auto',
      }}
    >
      <div
        style={{
          margin: '0',
          padding: '1em 1.5em',
          display: 'flex',
          justifyContent: 'flex-start',
          alignItems: 'center',
          gap: '1em',
        }}
      >
        <span
          style={{
            color: 'rgba(0, 0, 0, 0.88)',
            fontWeight: '600',
            fontSize: '16px',
            lineHeight: '1.5',
            wordWrap: 'break-word',
          }}
        >
          Replaced parameters by AI
        </span>
        <div style={{ flex: 1 }} />
        <Button
          icon={maximized ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
          size="small"
          type="text"
          onClick={() => {
            setMaximized(!maximized);
          }}
        />
        <Button type="text" size="small" onClick={onClose} icon={<CloseOutlined />} />
      </div>
      <div
        style={{
          padding: '0.5em 1.5em',
        }}
      >
        {!(previousParamDict && Object.keys(previousParamDict).length > 0) && (
          <div>No parameters changed by AI</div>
        )}
        {previousParamDict &&
          Object.keys(previousParamDict).length > 0 &&
          Object.keys(previousParamDict).map((key) => {
            return (
              <div key={key}>
                <div
                  style={{
                    color: 'rgba(0, 0, 0, 0.65)',
                    fontWeight: '600',
                    fontSize: '14px',
                    lineHeight: '2em',
                    wordWrap: 'break-word',
                  }}
                >
                  {key}
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-start',
                    alignItems: 'center',
                    borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                    lineHeight: '2em',
                    gap: '1em',
                  }}
                >
                  <span
                    style={{
                      color: 'rgba(0, 0, 0, 0.88)',
                      fontWeight: '600',
                      fontSize: '13px',
                      wordWrap: 'break-word',
                    }}
                  >
                    Previous:
                  </span>
                  <span
                    style={{
                      color: 'rgba(0, 0, 0, 0.88)',
                      fontWeight: '400',
                      fontSize: '14px',
                      wordWrap: 'break-word',
                    }}
                  >
                    {previousParamDict[key] === null && 'null'}
                    {previousParamDict[key] === undefined && 'undefined'}
                    {previousParamDict[key] !== null &&
                      previousParamDict[key] !== undefined &&
                      previousParamDict[key]}
                  </span>
                </div>
              </div>
            );
          })}
      </div>
    </div>
  );
};

export default PreviousParameter;
