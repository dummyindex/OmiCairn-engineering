// Adapted from cellxgene (https://github.com/chanzuckerberg/cellxgene),
// Copyright (c) Chan Zuckerberg Initiative. MIT License; see THIRD_PARTY_NOTICES.md.
import React from 'react';

const ErrorLoading = ({ displayName, zebra }) => (
  <div
    style={{
      backgroundColor: zebra ? 'grey' : 'white',
      fontStyle: 'italic',
    }}
  >
    <span>{`Failure loading ${displayName}`}</span>
  </div>
);

export default ErrorLoading;
