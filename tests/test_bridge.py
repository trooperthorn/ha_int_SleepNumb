"""Input validation contract for the hub bridge's command invocation.

The bridge runs on the rooted hub as Python 2.7, so it is loaded from its
file path here rather than imported as a package.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

BRIDGE_PATH = Path(__file__).resolve().parents[1] / "bridge" / "sleepnumber_bridge.py"


def _load_bridge():
    spec = importlib.util.spec_from_file_location("sleepnumber_bridge", BRIDGE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def bridge():
    return _load_bridge()


def test_build_argv_uses_a_list_without_a_shell(bridge) -> None:
    assert bridge.build_argv("PSNL", "") == ["/bam/scripts/bio", "PSNL"]
    assert bridge.build_argv("PSNS", "L100") == ["/bam/scripts/bio", "PSNS", "L100"]


def test_every_documented_key_is_accepted(bridge) -> None:
    for key in ("PSNL", "PSNR", "PSNS", "LBPL", "LBPR", "MFUL", "MFFL", "FWSL", "SBAS"):
        assert bridge.build_argv(key)[-1] == key


@pytest.mark.parametrize(
    ("key", "arg"),
    [
        ("PSNL;id", ""),
        ("psnl", ""),
        ("PSN", ""),
        ("PSNLX", ""),
        ("PSNX", ""),
        ("PSNL", "45; reboot"),
        ("PSNL", "$(id)"),
        ("PSNL", "a" * 33),
        ("", ""),
    ],
)
def test_build_argv_rejects_shell_metacharacters_and_unknown_keys(bridge, key: str, arg: str) -> None:
    with pytest.raises(ValueError):
        bridge.build_argv(key, arg)


def test_run_key_never_invokes_a_shell(bridge) -> None:
    class FakeProc:
        returncode = 0

        def communicate(self):
            return (b"PSNL 45\n", None)

    with patch.object(bridge.subprocess, "Popen", return_value=FakeProc()) as popen:
        out, rc = bridge.run_key("PSNL", "")
    assert (out, rc) == ("PSNL 45", 0)
    argv = popen.call_args.args[0]
    assert isinstance(argv, list)
    assert popen.call_args.kwargs["shell"] is False
