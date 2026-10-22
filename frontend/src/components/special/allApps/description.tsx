const AppDescription = ({ app }) => {
  return (
    <div
      style={{
        height: '100%',
        width: '100%',
      }}
    >
      {/* {selectedApp?.tags.map((tag) => (
                              <Tag color="blue" key={tag}>
                                {tag}
                              </Tag>
                            ))} */}
      <pre
        style={{
          padding: '1em 0',
          height: '68vh',
          overflowY: 'auto',
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          overflowWrap: 'break-word',
        }}
      >
        {app?.description}
      </pre>
    </div>
  );
};

export default AppDescription;
