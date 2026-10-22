import { useState } from 'react';

const useSnapShot = () => {
  const [snapShot, setSnapShot] = useState({});

  return {
    snapShot,
    setSnapShot,
  };
};

export default useSnapShot;
