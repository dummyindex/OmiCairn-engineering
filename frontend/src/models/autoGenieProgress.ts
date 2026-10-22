import { useState } from 'react';

const useAutoGenieProgress = () => {
  const [isModalVisible, setIsModalVisible] = useState<boolean>(false);
  const [isDropdownVisible, setIsDropdownVisible] = useState<boolean>(false);
  const [selectedPlan, setSelectedPlan] = useState<any>(null);

  return {
    isModalVisible,
    setIsModalVisible,
    isDropdownVisible,
    setIsDropdownVisible,
    selectedPlan,
    setSelectedPlan,
  };
};

export default useAutoGenieProgress;
