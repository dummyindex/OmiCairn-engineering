import { useState } from 'react';

const useTopGenesUI = () => {
  const [showTopGenesEditModal, setShowTopGenesEditModal] = useState(false);

  const [editedTopGenesName, setEditedTopGenesName] = useState(null as string | null);

  return {
    showTopGenesEditModal,
    editedTopGenesName,
    setEditedTopGenesName,
    setShowTopGenesEditModal,
  };
};

export default useTopGenesUI;
