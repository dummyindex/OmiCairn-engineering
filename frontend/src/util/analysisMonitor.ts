import { requestAnalysisUpdatedRecord } from '@/request/analysis';

type AnalysisMonitorConfig = {
  // Polling interval, in seconds
  cycle: number;
};

type StartOptions = {
  analysisId: number | string;
  setAnalysisUpdatedTime: (updatedTime: any) => void;
};

const DefaultConfig = {
  CYCLE: 2,
};

class AnalysisMonitor {
  // Polling interval, in seconds
  cycle: number;
  // id of the analysis currently being monitored
  analysisId: string | null;
  // timer
  timer: any;
  // paused
  isPause: boolean;
  // parameters captured when monitoring started
  startOptions: StartOptions | null;
  // last-updated timestamp
  lastUpdatedTime: number | null;
  constructor(config: AnalysisMonitorConfig) {
    this.cycle = config.cycle | DefaultConfig.CYCLE;
    this.analysisId = null;
    this.isPause = true;
    this.timer = this.timer = setInterval(this.monitorUpdatedTime.bind(this), this.cycle * 1000);
    this.startOptions = null;
    this.lastUpdatedTime = null;
  }

  setAnalysisId(analysisId: string | number) {
    if (typeof analysisId === 'number') {
      this.analysisId = analysisId.toString();
    } else {
      this.analysisId = analysisId;
    }
  }

  // Compare the analysis panel's current state with the analysis's live info
  async monitorUpdatedTime() {
    if (this.isPause || !this.analysisId) {
      return;
    }
    const _analysisId = this.analysisId;
    try {
      const { data: updatedRecord } = await requestAnalysisUpdatedRecord(_analysisId);
      if (!updatedRecord) {
        return;
      }
      const { updatedTime } = updatedRecord;
      if (_analysisId !== this.analysisId) {
        return;
      }
      if (!this.lastUpdatedTime || this.lastUpdatedTime !== updatedTime) {
        this.lastUpdatedTime = updatedTime;
        this.startOptions?.setAnalysisUpdatedTime(updatedTime);
      }
    } catch (error: any) {
      console.error(error);
    }
  }

  // Start monitoring
  start(options: StartOptions) {
    this.startOptions = options;
    this.isPause = false;
    this.lastUpdatedTime = null;
    this.monitorUpdatedTime();
  }

  pause() {
    this.isPause = true;
    this.lastUpdatedTime = null;
  }
}

export const analysisMonitor = new AnalysisMonitor({
  cycle: 5,
});
