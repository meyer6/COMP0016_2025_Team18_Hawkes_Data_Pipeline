"""
Unit tests for app/core/config/app_config.py - AppConfig
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.config.app_config import AppConfig
from app.core.config.constants import ProcessingDefaults, UIConstants


class TestAppConfig:

    def test_default_values(self, temp_dir):
        config = AppConfig(model_path=str(temp_dir / 'model.pkl'))
        assert config.sample_every == ProcessingDefaults.SAMPLE_EVERY
        assert config.smoothing_window == ProcessingDefaults.SMOOTHING_WINDOW
        assert config.min_duration_sec == ProcessingDefaults.MIN_DURATION_SEC
        assert config.confidence_threshold == ProcessingDefaults.CONFIDENCE_THRESHOLD
        assert config.window_width == UIConstants.DEFAULT_WINDOW_WIDTH
        assert config.grid_columns == UIConstants.GRID_COLUMNS

    def test_load_from_json(self, temp_dir):
        config_path = temp_dir / 'config.json'
        data = {'sample_every': 10, 'smoothing_window': 20, 'log_level': 'WARNING'}
        config_path.write_text(json.dumps(data))

        config = AppConfig.load(config_path)
        assert config.sample_every == 10
        assert config.smoothing_window == 20
        assert config.log_level == 'WARNING'

    def test_load_nonexistent_returns_defaults(self, temp_dir):
        config = AppConfig.load(temp_dir / 'nonexistent.json')
        assert config.sample_every == ProcessingDefaults.SAMPLE_EVERY

    def test_load_invalid_json(self, temp_dir):
        config_path = temp_dir / 'bad.json'
        config_path.write_text('not valid json {{{')
        config = AppConfig.load(config_path)
        assert config.sample_every == ProcessingDefaults.SAMPLE_EVERY

    def test_load_filters_unknown_fields(self, temp_dir):
        config_path = temp_dir / 'config.json'
        data = {'sample_every': 10, 'unknown_field': 'ignored', 'another_bad': 42}
        config_path.write_text(json.dumps(data))

        config = AppConfig.load(config_path)
        assert config.sample_every == 10
        assert not hasattr(config, 'unknown_field')

    def test_save_and_load_roundtrip(self, temp_dir):
        config_path = temp_dir / 'config.json'
        original = AppConfig(
            model_path=str(temp_dir / 'model.pkl'),
            sample_every=7,
            smoothing_window=10,
            log_level='ERROR'
        )
        assert original.save(config_path) is True

        loaded = AppConfig.load(config_path)
        assert loaded.sample_every == 7
        assert loaded.smoothing_window == 10
        assert loaded.log_level == 'ERROR'

    def test_save_creates_json_file(self, temp_dir):
        config_path = temp_dir / 'config.json'
        config = AppConfig(model_path=str(temp_dir / 'model.pkl'))
        config.save(config_path)

        data = json.loads(config_path.read_text())
        assert 'sample_every' in data
        assert 'log_level' in data

    def test_validate_valid_config(self, temp_dir):
        model_path = temp_dir / 'model.pkl'
        model_path.touch()
        config = AppConfig(model_path=str(model_path))
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_missing_model(self, temp_dir):
        config = AppConfig(model_path=str(temp_dir / 'nonexistent.pkl'))
        errors = config.validate()
        assert any('Model file not found' in e for e in errors)

    def test_validate_bad_sample_every(self, temp_dir):
        model_path = temp_dir / 'model.pkl'
        model_path.touch()
        config = AppConfig(model_path=str(model_path), sample_every=0)
        errors = config.validate()
        assert any('sample_every' in e for e in errors)

    def test_validate_bad_confidence(self, temp_dir):
        model_path = temp_dir / 'model.pkl'
        model_path.touch()
        config = AppConfig(model_path=str(model_path), confidence_threshold=1.5)
        errors = config.validate()
        assert any('confidence_threshold' in e for e in errors)

    def test_validate_small_window(self, temp_dir):
        model_path = temp_dir / 'model.pkl'
        model_path.touch()
        config = AppConfig(model_path=str(model_path), window_width=400, window_height=300)
        errors = config.validate()
        assert any('Window dimensions' in e for e in errors)

    def test_validate_bad_log_level(self, temp_dir):
        model_path = temp_dir / 'model.pkl'
        model_path.touch()
        config = AppConfig(model_path=str(model_path), log_level='INVALID')
        errors = config.validate()
        assert any('log_level' in e for e in errors)

    def test_get_model_path(self, test_config):
        assert isinstance(test_config.get_model_path(), Path)

    def test_get_log_path(self, test_config):
        assert isinstance(test_config.get_log_path(), Path)

    # --- New tests for missing coverage ---

    def test_load_default_path_when_none(self):
        """Line 63: load() with config_path=None uses default project root / config.json"""
        fake_root = Path('/fake/project/root')
        fake_config_path = fake_root / 'config.json'
        with patch('app.core.config.app_config.PathConfig.get_project_root', return_value=fake_root):
            # The default config.json won't exist at the fake path, so it returns defaults
            config = AppConfig.load(None)
            assert config.sample_every == ProcessingDefaults.SAMPLE_EVERY

    def test_save_default_path_when_none(self, temp_dir):
        """Line 83: save() with config_path=None uses default project root / config.json"""
        with patch('app.core.config.app_config.PathConfig.get_project_root', return_value=temp_dir):
            config = AppConfig(model_path=str(temp_dir / 'model.pkl'))
            result = config.save(None)
            assert result is True
            # Verify the file was written at the default location
            default_path = temp_dir / 'config.json'
            assert default_path.exists()
            data = json.loads(default_path.read_text())
            assert 'sample_every' in data

    def test_save_ioerror_returns_false(self, temp_dir):
        """Lines 90-92: IOError in save() logs error and returns False"""
        config = AppConfig(model_path=str(temp_dir / 'model.pkl'))
        # Use a path that will trigger an IOError (non-existent deep directory)
        bad_path = temp_dir / 'nonexistent_dir' / 'subdir' / 'config.json'
        with patch('app.core.config.app_config.logger') as mock_logger:
            result = config.save(bad_path)
            assert result is False
            mock_logger.error.assert_called_once()
            assert 'Failed to save config' in mock_logger.error.call_args[0][0]

    def test_validate_bad_smoothing_window(self, temp_dir):
        """Line 110: smoothing_window < 1 produces error"""
        model_path = temp_dir / 'model.pkl'
        model_path.touch()
        config = AppConfig(model_path=str(model_path), smoothing_window=0)
        errors = config.validate()
        assert any('smoothing_window must be >= 1' in e for e in errors)

    def test_validate_negative_min_duration(self, temp_dir):
        """Line 113: min_duration_sec < 0 produces error"""
        model_path = temp_dir / 'model.pkl'
        model_path.touch()
        config = AppConfig(model_path=str(model_path), min_duration_sec=-1)
        errors = config.validate()
        assert any('min_duration_sec must be >= 0' in e for e in errors)

    def test_validate_bad_thumbnail_dimensions(self, temp_dir):
        """Line 119: thumbnail_width or thumbnail_height < 1 produces error"""
        model_path = temp_dir / 'model.pkl'
        model_path.touch()
        config = AppConfig(model_path=str(model_path), thumbnail_width=0, thumbnail_height=0)
        errors = config.validate()
        assert any('Thumbnail dimensions must be positive' in e for e in errors)

    def test_validate_bad_thumbnail_height_only(self, temp_dir):
        """Line 119: thumbnail_height < 1 with valid width also triggers error"""
        model_path = temp_dir / 'model.pkl'
        model_path.touch()
        config = AppConfig(model_path=str(model_path), thumbnail_width=400, thumbnail_height=0)
        errors = config.validate()
        assert any('Thumbnail dimensions must be positive' in e for e in errors)
