import os

from pipeline import delivery


def test_deliver_writes_html_and_is_dry_by_default(tmp_path):
    out = str(tmp_path / "r.html")
    res = delivery.deliver("<p>hi</p>", "slack text", out, recipient="x@y.com", slack_channel="#c")
    assert os.path.exists(out)
    assert open(out, encoding="utf-8").read() == "<p>hi</p>"
    assert res["email_sent"] is False and res["slack_posted"] is False
    assert res["email_to"] == "x@y.com" and res["slack_channel"] == "#c"
    assert res["html_path"] == out


def test_deliver_non_dry_run_hits_unwired_sender(tmp_path):
    out = str(tmp_path / "r.html")
    # With a real recipient and dry_run=False, the (intentionally unwired) sender raises.
    try:
        delivery.deliver("<p>hi</p>", "slack", out, recipient="x@y.com", dry_run=False)
        assert False, "expected NotImplementedError until the sender is wired"
    except NotImplementedError:
        pass
    # The HTML artifact is still written before any send is attempted.
    assert os.path.exists(out)
