import math


class LineCrossingTracker:
    def __init__(self, max_lost=10, iou_threshold=0.3):
        self.max_lost = max_lost
        self.iou_threshold = iou_threshold
        self.tracks = {}
        self.next_id = 1
        self.line_position = None

    def reset(self):
        self.tracks = {}
        self.next_id = 1

    def _iou(self, box_a, box_b):
        x_a = max(box_a[0], box_b[0])
        y_a = max(box_a[1], box_b[1])
        x_b = min(box_a[2], box_b[2])
        y_b = min(box_a[3], box_b[3])
        inter_w = max(0, x_b - x_a)
        inter_h = max(0, y_b - y_a)
        inter = inter_w * inter_h
        if inter <= 0:
            return 0.0
        area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
        area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
        denom = float(area_a + area_b - inter)
        if denom <= 0:
            return 0.0
        return inter / denom

    def update(self, detections, frame_shape):
        if self.line_position is None:
            self.line_position = frame_shape[0] // 2

        assigned_tracks = set()
        current_ids = list(self.tracks.keys())
        entry_delta = 0
        exit_delta = 0

        for track_id in current_ids:
            self.tracks[track_id]["updated"] = False

        for det in detections:
            bbox = det["bbox"]
            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0
            conf = float(det.get("confidence", 1.0))

            best_iou = 0.0
            best_id = None

            for track_id in current_ids:
                if track_id in assigned_tracks:
                    continue
                prev_bbox = self.tracks[track_id]["bbox"]
                score = self._iou(bbox, prev_bbox)
                if score > best_iou:
                    best_iou = score
                    best_id = track_id

            if best_id is not None and best_iou >= self.iou_threshold:
                track = self.tracks[best_id]
                last_side = track["side"]
                new_side = "above" if cy < self.line_position else "below"
                if last_side is not None and new_side != last_side:
                    if last_side == "below" and new_side == "above":
                        entry_delta += 1
                    elif last_side == "above" and new_side == "below":
                        exit_delta += 1
                track["bbox"] = bbox
                track["center"] = (cx, cy)
                track["side"] = new_side
                track["confidence"] = conf
                track["lost"] = 0
                track["updated"] = True
                assigned_tracks.add(best_id)
            else:
                track_id = self.next_id
                self.next_id += 1
                side = "above" if cy < self.line_position else "below"
                self.tracks[track_id] = {
                    "bbox": bbox,
                    "center": (cx, cy),
                    "side": side,
                    "lost": 0,
                    "updated": True,
                    "confidence": conf,
                }
                assigned_tracks.add(track_id)

        to_delete = []
        for track_id, track in self.tracks.items():
            if not track["updated"]:
                track["lost"] += 1
                if track["lost"] > self.max_lost:
                    to_delete.append(track_id)
        for track_id in to_delete:
            del self.tracks[track_id]

        return entry_delta, exit_delta
