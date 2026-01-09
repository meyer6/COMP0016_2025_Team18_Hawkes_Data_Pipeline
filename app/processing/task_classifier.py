import pandas as pd

from ..infrastructure.inference_loader import InferenceLoader

_video_inference = None


def _get_inference_module():
    global _video_inference
    if _video_inference is None:
        _video_inference = InferenceLoader.load_video_inference_module()
    return _video_inference


class TaskClassifier:

    def __init__(self):
        vi = _get_inference_module()
        self.model = vi.model
        self.device = vi.DEVICE

    def process_video(self, video_path, sample_every=30, smoothing_window=15,
                      min_duration_sec=5, batch_size=32, **kwargs):
        vi = _get_inference_module()

        df = vi.process_video(video_path, self.model, self.device,
                              sample_every=sample_every, batch_size=batch_size)
        df = vi.smooth_predictions(df, smoothing_window=smoothing_window)
        df = vi.enforce_min_duration(df, min_duration_sec=min_duration_sec)

        return df.to_dict('records')

    def aggregate_time_ranges(self, results):
        vi = _get_inference_module()
        df = pd.DataFrame(results)
        return vi.aggregate_time_ranges(df).to_dict('records')
