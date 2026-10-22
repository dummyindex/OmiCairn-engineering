import { useState } from 'react';

const useImportDataUI = () => {
    const [showImportDataUI, setShowImportDataUI] = useState<boolean>(false);

    const [targetAnalysisId, setTargetAnalysisId] = useState<string | null>(
        null
    );

    const [selectedIds, setSelectedIds] = useState<string[]>([]);

    const openImportDataUI = (analysisId: string) => {
        setTargetAnalysisId(analysisId);
        setShowImportDataUI(true);
    }

    const closeImportDataUI = () => {
        setTargetAnalysisId(null);
        setSelectedIds([]);
        setShowImportDataUI(false);
    }

    return {
        openImportDataUI,
        closeImportDataUI,
        setSelectedIds,
        selectedIds,
        targetAnalysisId,
        showImportDataUI,
    };
}

export default useImportDataUI;