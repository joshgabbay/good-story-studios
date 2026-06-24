#!/usr/bin/env python3
"""
Render a visual preview of the studio-contact directory exactly as the monthly
newsletter will show it (one "Studio Contact" box per studio), using the SAME
selection logic and HTML the routine uses.

This is a review/QA helper — it does NOT send anything. It lets you eyeball every
studio's resolved contact (and the 'unverified' tags) without running the cloud
routine. It also serves as a structural check: it asserts the assembled HTML is
tag-balanced.

Usage:
    python3 tools/preview_contacts.py            # -> /tmp/contacts_preview.html
    python3 tools/preview_contacts.py out.html   # custom output path
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_DATE = "Generated June 24, 2026"


def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


def select_contact(company):
    """Mirror _meta.selection_order in studio-contacts.json."""
    contacts = company["contacts"]
    confirmed = [c for c in contacts if c.get("status") == "confirmed"]
    if confirmed:
        return confirmed[0]
    primary = [c for c in contacts if c.get("primary")]
    if primary:
        return primary[0]
    partnerships = [c for c in contacts if c.get("role_type") == "partnerships"]
    if partnerships:
        return partnerships[0]
    return contacts[0]  # publicity / whatever is left


def email_part(contact):
    email = contact.get("email")
    if email:
        inner = (f'<a href="mailto:{email}" style="color:#6B90D9;text-decoration:none;">'
                 f'{email}</a>')
    else:
        inner = ('<span style="color:#7A7E8B;font-weight:600;">'
                 'Email: research via LinkedIn / CRM</span>')
    if contact.get("status") == "speculative":
        inner += (' <span style="font-size:11px;font-weight:700;color:#C49A1E;'
                  'background-color:#FFF3CE;border-radius:10px;padding:2px 8px;">unverified</span>')
    return inner


def contact_box(contact):
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
        'style="margin:0 0 18px 0;"><tbody><tr><td style="background-color:#FFFBEF;'
        'border:1.5px solid #F4E3A6;border-radius:12px;padding:13px 18px;">'
        '<p style="margin:0 0 4px 0;font-family:\'Nunito\',Arial,sans-serif;font-size:11px;'
        'font-weight:900;color:#C49A1E;text-transform:uppercase;letter-spacing:0.8px;">Studio Contact &#10022;</p>'
        f'<p style="margin:0;font-family:\'Nunito\',Arial,sans-serif;font-size:14px;font-weight:800;'
        f'color:#2D2D2D;line-height:1.45;">{contact["name"]} '
        f'<span style="font-weight:600;color:#7A7E8B;">&mdash; {contact["title"]}</span></p>'
        f'<p style="margin:4px 0 0 0;font-family:\'Nunito\',Arial,sans-serif;font-size:13px;'
        f'font-weight:700;line-height:1.5;">{email_part(contact)}</p>'
        '</td></tr></tbody></table>'
    )


def studio_block(studio_name, contact_html):
    return (
        '<table class="studio-block" role="presentation" cellpadding="0" cellspacing="0" '
        'border="0" width="100%" style="margin-bottom:36px;"><tbody><tr><td>'
        '<h2 style="margin:0 0 14px 0;font-family:\'Nunito\',Arial,sans-serif;font-size:20px;'
        'font-weight:900;color:#6B90D9;letter-spacing:-0.2px;border-left:5px solid #F2C53D;'
        f'padding-left:14px;line-height:1.2;">{studio_name}</h2>{contact_html}'
        '<p style="margin:0 0 4px 0;font-family:\'Nunito\',Arial,sans-serif;font-size:12px;'
        'font-style:italic;color:#B5BECF;">(film entries for this studio are generated each run)</p>'
        '</td></tr></tbody></table>'
    )


def assert_balanced(html):
    for tag in ("table", "tbody", "tr", "td", "p", "h2"):
        opens = html.count(f"<{tag} ") + html.count(f"<{tag}>")
        closes = html.count(f"</{tag}>")
        assert opens == closes, f"UNBALANCED <{tag}>: {opens} open vs {closes} close"
    for token in ("{{MONTH_YEAR}}", "{{STUDIO_BLOCKS}}", "{{GENERATED_DATE}}"):
        assert token not in html, f"unfilled template placeholder remains: {token}"


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/contacts_preview.html"
    contacts = load("studio-contacts.json")
    studios = load("studios.json")
    l2c = contacts["label_to_company"]
    companies = contacts["companies"]
    with open(os.path.join(HERE, "email-template.html"), encoding="utf-8") as f:
        template = f.read()

    blocks = []
    summary = []
    for s in studios["studios"]:
        key, name = s["key"], s["name"]
        company = companies[l2c[key]]
        c = select_contact(company)
        blocks.append(studio_block(name, contact_box(c)))
        flag = c.get("status")
        summary.append(f"  {name:<28} -> {c['name']} ({c['title'][:40]}...) [{flag}]")

    html = (template
            .replace("{{MONTH_YEAR}}", "Studio Contact Directory — Preview")
            .replace("{{GENERATED_DATE}}", GENERATED_DATE)
            .replace("{{STUDIO_BLOCKS}}", "\n".join(blocks)))

    assert_balanced(html)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("Resolved contact per studio (24):")
    print("\n".join(summary))
    print(f"\nHTML is tag-balanced. Wrote preview -> {out_path} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
