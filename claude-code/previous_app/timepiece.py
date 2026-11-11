from datetime import datetime, timedelta

class TimePiece:
    def __init__(self) -> None:
        self.duration_dict = dict()

    def start_duration(self, duration_name: str):
        now = datetime.now()
        self.duration_dict[duration_name] = {
            "start": now,
            "end": now
        }
    
    def end_duration(self, duration_name: str):
        now = datetime.now()
        if duration_name not in self.duration_dict:
            raise Exception(f"duration {duration_name} not started")
        self.duration_dict[duration_name]["end"] = now

    def get_duration_length(self, duration_name: str) -> timedelta:
        if duration_name not in self.duration_dict:
            raise Exception(f"duration {duration_name} not started")
        return self.duration_dict[duration_name]["end"] - self.duration_dict[duration_name]["start"]
    
    def get_duration_reports(self):
        reports = []
        for duration_name in self.duration_dict:
            reports.append({
                "name": duration_name,
                "start": self.duration_dict[duration_name]["start"].strftime("%Y-%m-%d %H:%M:%S"),
                "end": self.duration_dict[duration_name]["end"].strftime("%Y-%m-%d %H:%M:%S"),
                "length": self.get_duration_length(duration_name).total_seconds()
            })
        reports.sort(key=lambda x: x["start"])
        return reports