import argparse
import json

from pipeline import transform, engine, relationships, report, delivery


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _build_narrative(report_data):
    if report_data["is_baseline"]:
        return "Baseline month — establishing the comparison point for future reports."
    if not report_data["ranked"]:
        return "No long-form sponsorships found this month."
    top = report_data["ranked"][0]
    bits = ["%s leads with %d sponsorships (%s vs prior month)." %
            (top["brand_display"], top["count"], top["direction"])]
    if report_data["new_brands"]:
        bits.append("New entrants: " + ", ".join(b["brand_display"] for b in report_data["new_brands"]) + ".")
    if report_data["dropped_brands"]:
        bits.append("Dropped off: " + ", ".join(b["brand_display"] for b in report_data["dropped_brands"]) + ".")
    return " ".join(bits)


def run_month(csv_path, month, config_path, aliases_path, known_brands_path,
              template_path, db_path, out_html_path, month_label, generated_date):
    config = _load_json(config_path)
    aliases = _load_json(aliases_path)
    known = relationships.load_known_brands(known_brands_path)

    raw = transform.load_csv(csv_path, config["column_map"])
    rows = transform.normalize_rows(raw, month, config, aliases)

    conn = engine.connect(db_path)
    engine.init_schema(conn)
    engine.load_month(conn, month, rows)
    report_data = engine.rank_and_diff(conn, month, config["top_n"])
    report_data["unmatched"] = transform.top_unmatched_brands(rows, exclude=set(known))
    report_data["warning"] = transform.long_form_warning(raw, config)

    rels = relationships.lookup_relationships(
        [r["brand_canonical"] for r in report_data["ranked"]], known)
    narrative = _build_narrative(report_data)

    # External (client) recipients don't get the internal alias-review section.
    show_unmatched = config.get("audience", "internal") != "external"

    with open(template_path, encoding="utf-8") as fh:
        template = fh.read()
    html = report.render_html(report_data, rels, template, month_label, generated_date,
                              narrative, show_unmatched=show_unmatched)
    slack_text = report.render_slack(report_data, rels, month_label)

    # Delivery is dry-run in v1: writes the HTML artifact; email/Slack senders are wired later.
    delivery_result = delivery.deliver(
        html, slack_text, out_html_path,
        recipient=config.get("final_recipient"),
        slack_channel=config.get("slack_channel"),
        dry_run=True,
    )
    print(slack_text)
    return {"report": report_data, "relationships": rels, "html_path": out_html_path,
            "slack_text": slack_text, "delivery": delivery_result}


def main(argv=None):
    p = argparse.ArgumentParser(description="YouTube Sponsorship Intelligence monthly run")
    p.add_argument("--csv", required=True)
    p.add_argument("--month", required=True, help="YYYY-MM")
    p.add_argument("--config", default="config.json")
    p.add_argument("--aliases", default="brand_aliases.seed.json")
    p.add_argument("--known-brands", default="known_brands.json")
    p.add_argument("--template", default="email-template.html")
    p.add_argument("--db", default="history.db")
    p.add_argument("--out", default="report.html")
    p.add_argument("--month-label", required=True)
    p.add_argument("--generated-date", required=True)
    a = p.parse_args(argv)
    run_month(a.csv, a.month, a.config, a.aliases, a.known_brands, a.template,
              a.db, a.out, a.month_label, a.generated_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
