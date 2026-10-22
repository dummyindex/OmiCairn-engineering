import DynamicGenerationTaskCardCollapsed from '@/components/common/dynamicGenerationTaskCardCollapsed';
import { requestDynamicGenerationListByAnalysis } from '@/request/computation';
import React, { useEffect, useRef, useState } from 'react';
import { useModel } from 'umi';
import './autoGenieProcessTab.css';

interface DynamicGenerationTask {
  generationId: number;
  userRequest: string;
  state: string;
  createdTime: number;
}

interface AutoGenieProcessTabProps {
  analysisId?: string;
  targetGenerationId?: number | null;
}

const AutoGenieProcessTab: React.FC<AutoGenieProcessTabProps> = ({
  analysisId,
  targetGenerationId,
}) => {
  const { dictionary } = useModel('localization');

  // const { currentSelectedNodes } = useModel("analysis");

  // Auto Genie Process states
  const [dynamicGenerationTasks, setDynamicGenerationTasks] = useState<DynamicGenerationTask[]>([]);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const lastScrolledIdRef = useRef<number | null>(null);

  const fetchDynamicGenerationTasks = async () => {
    if (!analysisId) return;

    try {
      const response = await requestDynamicGenerationListByAnalysis(analysisId);
      if (response.code === 200 && response.data) {
        const sortedTasks = response.data.sort(
          (a: DynamicGenerationTask, b: DynamicGenerationTask) =>
            b.createdTime > a.createdTime ? 1 : -1,
        );
        setDynamicGenerationTasks(sortedTasks);
      }
    } catch (error) {
      console.error('Failed to fetch dynamic generation task list:', error);
    }
  };

  const startPolling = () => {
    fetchDynamicGenerationTasks();
    pollingRef.current = setInterval(() => {
      // 1. Update the task list
      fetchDynamicGenerationTasks();
    }, 3000);
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => {
    if (analysisId) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [analysisId]);

  useEffect(() => {
    if (
      targetGenerationId &&
      targetGenerationId !== lastScrolledIdRef.current &&
      dynamicGenerationTasks.length > 0
    ) {
      const targetTask = dynamicGenerationTasks.find(
        (task) => task.generationId === targetGenerationId,
      );
      if (targetTask) {
        setTimeout(() => {
          const element = document.getElementById(`auto-genie-task-${targetGenerationId}`);
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            lastScrolledIdRef.current = targetGenerationId;
          } else {
            lastScrolledIdRef.current = null;
          }
        }, 200);
      }
    }
  }, [targetGenerationId, dynamicGenerationTasks]);

  return (
    <div>
      {dynamicGenerationTasks.length === 0 ? (
        <div
          style={{
            padding: '40px',
            textAlign: 'center',
            color: '#999',
            background: 'white',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
          }}
        >
          {dictionary.NO_DYNAMIC_GENERATION_TASKS || 'No dynamic generation tasks'}
        </div>
      ) : (
        dynamicGenerationTasks.map((task) => {
          return (
            <div key={task.generationId} id={`auto-genie-task-${task.generationId}`}>
              <DynamicGenerationTaskCardCollapsed
                task={task}
                isHighlighted={task.generationId === targetGenerationId}
              />
            </div>
          );
        })
      )}
    </div>
  );
};

export default AutoGenieProcessTab;
