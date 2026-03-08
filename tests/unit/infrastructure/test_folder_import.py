"""
Unit tests for app/infrastructure/folder_import.py
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.infrastructure.folder_import import validate_folder, concatenate_parts


class TestValidateFolder:

    def test_not_a_directory(self, temp_dir):
        fake_path = str(temp_dir / 'nonexistent')
        result = validate_folder(fake_path)
        assert result.is_err()
        assert "Not a directory" in result.unwrap_err().message

    def test_no_part_subfolders(self, temp_dir):
        # Directory exists but has no partXXXX subfolders
        (temp_dir / 'random_folder').mkdir()
        result = validate_folder(str(temp_dir))
        assert result.is_err()
        assert "No partXXXX subfolders" in result.unwrap_err().message

    def test_missing_video_in_part(self, temp_dir):
        # part0001 exists but has no EndoscopeImageMemory_0.avi
        (temp_dir / 'part0001').mkdir()
        result = validate_folder(str(temp_dir))
        assert result.is_err()
        assert "Missing EndoscopeImageMemory_0.avi" in result.unwrap_err().message
        assert "part0001" in result.unwrap_err().message

    def test_valid_single_part(self, temp_dir):
        part_dir = temp_dir / 'part0001'
        part_dir.mkdir()
        (part_dir / 'EndoscopeImageMemory_0.avi').touch()

        result = validate_folder(str(temp_dir))
        assert result.is_ok()
        paths = result.unwrap()
        assert len(paths) == 1
        assert 'EndoscopeImageMemory_0.avi' in paths[0]

    def test_valid_multiple_parts_sorted(self, temp_dir):
        # Create parts out of order
        for num in [3, 1, 2]:
            part_dir = temp_dir / f'part{num:04d}'
            part_dir.mkdir()
            (part_dir / 'EndoscopeImageMemory_0.avi').touch()

        result = validate_folder(str(temp_dir))
        assert result.is_ok()
        paths = result.unwrap()
        assert len(paths) == 3
        assert 'part0001' in paths[0]
        assert 'part0002' in paths[1]
        assert 'part0003' in paths[2]

    def test_ignores_non_part_directories(self, temp_dir):
        # Non-matching directories should be ignored
        (temp_dir / 'other_dir').mkdir()
        (temp_dir / 'notpart1').mkdir()
        part_dir = temp_dir / 'part0001'
        part_dir.mkdir()
        (part_dir / 'EndoscopeImageMemory_0.avi').touch()

        result = validate_folder(str(temp_dir))
        assert result.is_ok()
        assert len(result.unwrap()) == 1

    def test_case_insensitive_part_matching(self, temp_dir):
        part_dir = temp_dir / 'Part0001'
        part_dir.mkdir()
        (part_dir / 'EndoscopeImageMemory_0.avi').touch()

        result = validate_folder(str(temp_dir))
        assert result.is_ok()

    def test_multiple_missing_parts_listed(self, temp_dir):
        (temp_dir / 'part0001').mkdir()
        (temp_dir / 'part0002').mkdir()
        result = validate_folder(str(temp_dir))
        assert result.is_err()
        err_msg = result.unwrap_err().message
        assert 'part0001' in err_msg
        assert 'part0002' in err_msg


class TestConcatenateParts:

    @patch('app.infrastructure.folder_import.subprocess.run')
    def test_success(self, mock_run, temp_dir):
        mock_run.return_value = MagicMock(returncode=0)
        output_path = temp_dir / 'output.avi'
        # Simulate ffmpeg creating the file
        def create_output(*args, **kwargs):
            output_path.touch()
            return MagicMock(returncode=0)
        mock_run.side_effect = create_output

        result = concatenate_parts(['/a/part1.avi', '/b/part2.avi'], str(output_path))
        assert result.is_ok()
        assert result.unwrap() == str(output_path)

    @patch('app.infrastructure.folder_import.subprocess.run')
    def test_ffmpeg_nonzero_exit(self, mock_run, temp_dir):
        mock_run.return_value = MagicMock(returncode=1)
        output_path = temp_dir / 'output.avi'

        result = concatenate_parts(['/a.avi'], str(output_path))
        assert result.is_err()
        assert "exit code 1" in result.unwrap_err().message

    @patch('app.infrastructure.folder_import.subprocess.run')
    def test_output_not_created(self, mock_run, temp_dir):
        mock_run.return_value = MagicMock(returncode=0)
        output_path = temp_dir / 'output.avi'
        # Don't create file — simulates ffmpeg succeeding but no output

        result = concatenate_parts(['/a.avi'], str(output_path))
        assert result.is_err()
        assert "not created" in result.unwrap_err().message

    @patch('app.infrastructure.folder_import.subprocess.run')
    def test_ffmpeg_not_found(self, mock_run, temp_dir):
        mock_run.side_effect = FileNotFoundError()
        output_path = temp_dir / 'output.avi'

        result = concatenate_parts(['/a.avi'], str(output_path))
        assert result.is_err()
        assert "FFmpeg not found" in result.unwrap_err().message

    @patch('app.infrastructure.folder_import.subprocess.run')
    def test_generic_exception(self, mock_run, temp_dir):
        mock_run.side_effect = RuntimeError("something broke")
        output_path = temp_dir / 'output.avi'

        result = concatenate_parts(['/a.avi'], str(output_path))
        assert result.is_err()
        assert "something broke" in result.unwrap_err().message

    @patch('app.infrastructure.folder_import.subprocess.run')
    def test_creates_parent_directories(self, mock_run, temp_dir):
        mock_run.return_value = MagicMock(returncode=0)
        output_path = temp_dir / 'nested' / 'deep' / 'output.avi'

        def create_output(*args, **kwargs):
            output_path.touch()
            return MagicMock(returncode=0)
        mock_run.side_effect = create_output

        result = concatenate_parts(['/a.avi'], str(output_path))
        assert result.is_ok()
        assert (temp_dir / 'nested' / 'deep').exists()

    @patch('app.infrastructure.folder_import.subprocess.run')
    def test_concat_list_cleaned_up(self, mock_run, temp_dir):
        """Temp concat list file is cleaned up in finally block"""
        mock_run.return_value = MagicMock(returncode=0)
        output_path = temp_dir / 'output.avi'
        output_path.touch()

        with patch('app.infrastructure.folder_import.tempfile.NamedTemporaryFile') as mock_tmp:
            tmp_path = str(temp_dir / 'concat_list.txt')
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_file.name = tmp_path
            mock_tmp.return_value = mock_file

            # Create the temp file so unlink works
            Path(tmp_path).touch()

            result = concatenate_parts(['/a.avi'], str(output_path))
            assert result.is_ok()
            # Temp file should have been cleaned up
            assert not Path(tmp_path).exists()

    @patch('app.infrastructure.folder_import.subprocess.run')
    def test_cleanup_exception_suppressed(self, mock_run, temp_dir):
        """Exception during temp file cleanup is suppressed"""
        mock_run.return_value = MagicMock(returncode=0)
        output_path = temp_dir / 'output.avi'
        output_path.touch()

        with patch('app.infrastructure.folder_import.Path.unlink', side_effect=PermissionError):
            result = concatenate_parts(['/a.avi'], str(output_path))
            # Should not raise, cleanup exception is suppressed
            assert result.is_ok()

    @patch('app.infrastructure.folder_import.sys')
    @patch('app.infrastructure.folder_import.subprocess')
    def test_win32_creation_flags(self, mock_subprocess, mock_sys, temp_dir):
        mock_sys.platform = 'win32'
        mock_subprocess.CREATE_NO_WINDOW = 0x08000000
        mock_subprocess.DEVNULL = subprocess.DEVNULL
        output_path = temp_dir / 'output.avi'

        def create_and_check(*args, **kwargs):
            assert 'creationflags' in kwargs
            assert kwargs['creationflags'] == 0x08000000
            output_path.touch()
            return MagicMock(returncode=0)

        mock_subprocess.run.side_effect = create_and_check
        result = concatenate_parts(['/a.avi'], str(output_path))
        assert result.is_ok()

    @patch('app.infrastructure.folder_import.sys')
    @patch('app.infrastructure.folder_import.subprocess.run')
    def test_non_win32_no_creation_flags(self, mock_run, mock_sys, temp_dir):
        mock_sys.platform = 'linux'
        output_path = temp_dir / 'output.avi'

        def create_and_check(*args, **kwargs):
            assert 'creationflags' not in kwargs
            output_path.touch()
            return MagicMock(returncode=0)

        mock_run.side_effect = create_and_check
        result = concatenate_parts(['/a.avi'], str(output_path))
        assert result.is_ok()

    @patch('app.infrastructure.folder_import.subprocess.run')
    def test_path_with_single_quote(self, mock_run, temp_dir):
        """Paths with single quotes are escaped in concat list"""
        mock_run.return_value = MagicMock(returncode=0)
        output_path = temp_dir / 'output.avi'
        output_path.touch()

        result = concatenate_parts(["/path/it's/video.avi"], str(output_path))
        assert result.is_ok()
