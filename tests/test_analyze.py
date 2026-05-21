import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.core.analyze import ScanCache, get_rust_scan_data, get_dir_size_recursive

def test_scan_cache():
    """Verify that ScanCache stores and retrieves data correctly."""
    path = Path("/tmp/test_path")
    data = {"total_size_bytes": 1024}
    
    ScanCache.set(path, data)
    assert ScanCache.get(path) == data
    
    # Check that a different path returns None
    assert ScanCache.get(Path("/tmp/other")) is None

@patch("subprocess.run")
def test_get_rust_scan_data_success(mock_run):
    """Verify parsing of Rust engine output."""
    mock_data = {
        "path": "/home/user",
        "total_size_bytes": 5000,
        "file_count": 10,
        "subdirs": {"docs": 2000, "pics": 3000},
        "top_files": []
    }
    
    # Mock successful subprocess run
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(mock_data)
    )
    
    # We need to mock Path.exists for the binary
    with patch("pathlib.Path.exists", return_value=True):
        result = get_rust_scan_data(Path("/home/user"))
        assert result == mock_data
        # Verify it was cached
        assert ScanCache.get(Path("/home/user")) == mock_data

@patch("subprocess.run")
def test_get_dir_size_recursive_fallback(mock_run):
    """Verify fallback to 'du' if Rust engine fails."""
    # 1. Rust scan fails (return None)
    with patch("src.core.analyze.get_rust_scan_data", return_value=None):
        # 2. Mock 'du' output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="12345\t/some/path"
        )
        
        size = get_dir_size_recursive(Path("/some/path"))
        assert size == 12345
        assert "du" in mock_run.call_args[0][0]
