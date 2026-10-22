const RightSider = () => {
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        overflowY: 'auto',
        padding: '1em',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start',
        paddingTop: '5em',
        gap: '2em',
      }}
    >
      <div
        style={{
          backgroundColor: 'white',
          width: '100%',
          height: '20vh',
          borderRadius: '0.5em',
        }}
      />

      <div
        style={{
          backgroundColor: 'white',
          width: '100%',
          height: '20vh',
          borderRadius: '0.5em',
        }}
      />
    </div>
  );
};

export default RightSider;
