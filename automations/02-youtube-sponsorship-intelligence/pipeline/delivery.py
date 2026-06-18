"""Delivery layer for the monthly report.

v1 is a dry-run stub: it writes the HTML artifact and reports what *would* be sent, but does
not actually send. Wire the two senders below when the connectors exist — `run.py` and the
rest of the pipeline never change, because the `deliver()` signature stays fixed.
"""


def deliver(html, slack_text, out_html_path, recipient=None, slack_channel=None, dry_run=True):
    """Write the report HTML and dispatch it.

    Returns a result dict describing what was (or would be) sent. In v1 (`dry_run=True`, the
    default) nothing is actually sent — only the HTML file is written.
    """
    with open(out_html_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    result = {
        "html_path": out_html_path,
        "email_to": recipient,
        "slack_channel": slack_channel,
        "email_sent": False,
        "slack_posted": False,
    }
    if dry_run:
        return result

    if recipient:
        result["email_sent"] = _send_email_via_supabase(recipient, html)
    if slack_channel:
        result["slack_posted"] = _post_to_slack(slack_channel, slack_text)
    return result


# --- Wire these when the connectors exist (signatures are fixed so callers never change) ---

def _send_email_via_supabase(recipient, html):  # pragma: no cover - wired at deploy
    raise NotImplementedError(
        "Wire to the Supabase email_queue + send edge function (same pattern as the film-slate "
        "automation) at deploy time."
    )


def _post_to_slack(channel, text):  # pragma: no cover - wired at deploy
    raise NotImplementedError("Wire to the Slack connector at deploy time.")
