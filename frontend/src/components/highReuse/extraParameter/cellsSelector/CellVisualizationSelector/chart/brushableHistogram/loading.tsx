// Adapted from cellxgene (https://github.com/chanzuckerberg/cellxgene),
// Copyright (c) Chan Zuckerberg Initiative. MIT License; see THIRD_PARTY_NOTICES.md.
import React from 'react';
// import { Button } from 'antd';

const StillLoading = ({ zebra, displayName }) => (
  /*
    Render a loading indicator for the field.
    */
  <div
    style={{
      padding: '10px 12px',
      backgroundColor: zebra ? 'grey' : 'white',
    }}
  >
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        justifyItems: 'center',
        alignItems: 'center',
      }}
    >
      <div style={{ minWidth: 30 }} />
      <div style={{ display: 'flex', alignSelf: 'center' }}>
        <span style={{ fontStyle: 'italic' }}>{displayName}</span>
      </div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        {/* <Button
          size="small"
          loading
          type="primary"
        /> */}
      </div>
    </div>
  </div>
);
export default StillLoading;
