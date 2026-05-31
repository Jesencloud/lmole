from src.core.history import parse_deletion_history, render_history


def test_parse_session_history(tmp_path):
    log = tmp_path / "deletions.log"
    log.write_text(
        "\n".join(
            [
                "2026-05-31T10:00:00+08:00\tsession\t0\tstarted\tclean",
                "2026-05-31T10:00:01+08:00\tpermanent\t1024\tdeleted\t/tmp/a",
                "2026-05-31T10:00:02+08:00\ttrash\t2048\ttrashed-gio\t/tmp/b",
                "2026-05-31T10:00:03+08:00\tpermanent\tunknown\tfailed\t/tmp/c",
                "2026-05-31T10:00:04+08:00\tsession\t0\tended\tclean",
            ]
        )
    )

    sessions = parse_deletion_history(log)

    assert len(sessions) == 1
    session = sessions[0]
    assert session.command == "clean"
    assert session.removed == 1
    assert session.trashed == 1
    assert session.failed == 1
    assert session.skipped == 0
    assert session.total_size == 3072


def test_parse_legacy_ungrouped_history(tmp_path):
    log = tmp_path / "deletions.log"
    log.write_text(
        "\n".join(
            [
                "2026-05-31T11:00:01+08:00\tpermanent\t100\tdeleted\t/tmp/a",
                "2026-05-31T11:00:02+08:00\tpermanent\t0\trejected-validation\t/etc/passwd",
            ]
        )
    )

    sessions = parse_deletion_history(log)

    assert len(sessions) == 1
    assert sessions[0].command == "legacy"
    assert sessions[0].removed == 1
    assert sessions[0].skipped == 1


def test_render_history_summary(tmp_path):
    log = tmp_path / "deletions.log"
    log.write_text(
        "\n".join(
            [
                "2026-05-31T10:00:00+08:00\tsession\t0\tstarted\tclean",
                "2026-05-31T10:00:01+08:00\tpermanent\t1024\tdeleted\t/tmp/a",
                "2026-05-31T10:00:02+08:00\tsession\t0\tended\tclean",
            ]
        )
    )

    output = render_history(parse_deletion_history(log))

    assert "Deletion History" in output
    assert "removed=1" in output
    assert "size=1.0 KiB" in output
