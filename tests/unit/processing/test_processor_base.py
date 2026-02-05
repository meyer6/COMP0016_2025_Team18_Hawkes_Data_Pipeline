"""
Unit tests for app/processing/base/processor_base.py
"""

import pytest

from app.processing.base.processor_base import ProcessorBase


class TestProcessorBase:

    def test_cannot_instantiate_abstract(self):
        """Line 33: ProcessorBase is abstract"""
        with pytest.raises(TypeError):
            ProcessorBase()

    def test_subclass_must_implement(self):
        class BadProcessor(ProcessorBase):
            pass
        with pytest.raises(TypeError):
            BadProcessor()

    def test_subclass_works(self):
        class GoodProcessor(ProcessorBase):
            def process_video(self, video_path, progress_callback=None):
                return None
        proc = GoodProcessor()
        assert proc.process_video('/test.mp4') is None
