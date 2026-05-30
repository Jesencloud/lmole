import subprocess
from unittest.mock import MagicMock, patch

from src.core.system import run_command


@patch("subprocess.run")
def test_run_command_success_result(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

    result = run_command(["echo", "ok"], timeout=5)

    assert result.ok is True
    assert result.returncode == 0
    assert result.stdout == "ok"
    mock_run.assert_called_with(
        ["echo", "ok"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )


@patch("subprocess.run")
def test_run_command_failure_result(mock_run):
    mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="bad")

    result = run_command(["false"], timeout=5)

    assert result.ok is False
    assert result.returncode == 2
    assert result.stderr == "bad"


@patch("subprocess.run")
def test_run_command_timeout_result(mock_run):
    mock_run.side_effect = subprocess.TimeoutExpired(["slow"], timeout=1, output=b"partial")

    result = run_command(["slow"], timeout=1)

    assert result.ok is False
    assert result.returncode == 124
    assert result.timed_out is True
    assert result.stdout == "partial"
