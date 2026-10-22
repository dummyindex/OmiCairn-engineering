import { Card, Drawer } from 'antd';

const HistoryChatListDrawer = ({ showHistory, setShowHistory, chatList, setChatId }) => {
  return (
    <Drawer
      title="Chat History"
      placement="left"
      onClose={() => setShowHistory(false)}
      open={showHistory}
      width={360}
    >
      {chatList.map((item) => (
        <Card
          key={item.id}
          size="small"
          style={{ marginBottom: '12px', cursor: 'pointer' }}
          hoverable
          onClick={() => {
            console.log('Switching to chat ID:', item.id);
            setChatId(item.id);
            setShowHistory(false);
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{item.title}</div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                #{item.id} {item.name}
              </div>
              <div
                style={{
                  fontSize: '12px',
                  color: '#999',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {item.updatedTime}
              </div>
            </div>
          </div>
        </Card>
      ))}
    </Drawer>
  );
};

export default HistoryChatListDrawer;
