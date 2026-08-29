"""Build the Andexa cards site.

Reads people/<slug>/card.json (+ optional photo.jpg/photo.png), renders
template/card.html for each person, generates their vCard (photo embedded
when available), and writes everything to site/ ready for GitHub Pages.

Run from the repo root: python tools/build.py
"""

import base64
import html
import io
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PEOPLE = ROOT / "people"
SITE = ROOT / "site"
DOMAIN = "card.andexa.tech"

try:
    from PIL import Image
except ImportError:
    print("Pillow is required: pip install pillow", file=sys.stderr)
    sys.exit(1)


def fold(line: str, limit: int = 75) -> list[str]:
    """vCard 3.0 line folding: continuation lines start with one space."""
    out = [line[:limit]]
    line = line[limit:]
    while line:
        out.append(" " + line[: limit - 1])
        line = line[limit - 1 :]
    return out


def build_vcf(p: dict, photo: Path | None) -> str:
    v = p["vcard"]
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N;CHARSET=UTF-8:{v['family']};{v['given']};{v.get('middle', '')};;",
        f"FN;CHARSET=UTF-8:{p['full_name_en']}",
    ]
    if p.get("phonetic_first_ar"):
        lines.append(f"X-PHONETIC-FIRST-NAME;CHARSET=UTF-8:{p['phonetic_first_ar']}")
    if p.get("phonetic_last_ar"):
        lines.append(f"X-PHONETIC-LAST-NAME;CHARSET=UTF-8:{p['phonetic_last_ar']}")
    lines += [
        f"ORG;CHARSET=UTF-8:{p['org']}",
        f"TITLE;CHARSET=UTF-8:{p['title_en']}",
        f"TEL;TYPE=CELL:{p['phone']}",
    ]
    if p.get("email"):
        lines.append(f"EMAIL;TYPE=WORK:{p['email']}")
    if p.get("website"):
        lines.append(f"URL:{p['website']}")
    if p.get("linkedin"):
        lines += [f"item1.URL:{p['linkedin']}", "item1.X-ABLabel:LinkedIn"]
    if photo:
        im = Image.open(photo).convert("RGB")
        im.thumbnail((320, 320), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=82, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        lines.append("PHOTO;ENCODING=b;TYPE=JPEG:" + b64)
    lines += [f"NOTE;CHARSET=UTF-8:{p['notes']}", "END:VCARD"]
    folded: list[str] = []
    for line in lines:
        folded.extend(fold(line))
    return "\r\n".join(folded) + "\r\n"


def render_card(template: str, p: dict, slug: str, has_photo: bool) -> str:
    if has_photo:
        portrait = (
            f'<div class="portrait"><img src="photo.jpg" '
            f'alt="{html.escape(p["name_en"])}"></div>'
        )
    else:
        portrait = (
            '<div class="portrait seal" aria-hidden="true">'
            f'<span data-ar="{html.escape(p["monogram_ar"])}" '
            f'data-en="{html.escape(p["monogram_en"])}">'
            f'{html.escape(p["monogram_en"])}</span></div>'
        )
    card_json = json.dumps(
        {
            "url": "",  # empty = the page's own URL (QR + Android fallback)
            "phone": p["phone"],
            "whatsapp": p.get("whatsapp", ""),
            "email": p.get("email", ""),
            "website": p.get("website", ""),
            "linkedin": p.get("linkedin", ""),
            "fullName": p["full_name_en"],
            "jobTitle": p["title_en"],
            "org": p["org"],
            "notes": p["notes"],
            "vcf": f"{slug}.vcf",
        },
        ensure_ascii=False,
    )
    tokens = {
        "{{NAME_EN}}": html.escape(p["name_en"]),
        "{{NAME_AR}}": html.escape(p["name_ar"]),
        "{{TITLE_AR}}": html.escape(p["title_ar"]),
        "{{TITLE_EN_ATTR}}": html.escape(p["title_en"]),
        "{{TITLE_EN_HTML}}": html.escape(p["title_en"]),
        "{{ORG_EN}}": html.escape(p["org"]),
        "{{ORG_AR}}": html.escape(p["org_ar"]),
        "{{PORTRAIT}}": portrait,
        "{{VCF_FILE}}": f"{slug}.vcf",
        "{{VCF_DOWNLOAD}}": f"{p['full_name_en'].replace(' ', '-')}.vcf",
        "{{CARD_JSON}}": card_json,
    }
    out = template
    for k, val in tokens.items():
        out = out.replace(k, val)
    return out


def render_directory(entries: list[dict]) -> str:
    rows = "\n".join(
        f'      <a class="person" href="/{e["slug"]}/">'
        f'<strong>{html.escape(e["name_en"])}</strong>'
        f'<span>{html.escape(e["title_en"])}</span></a>'
        for e in entries
    )
    return f"""<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Andexa — Team cards</title>
<meta name="theme-color" content="#0E1412">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=IBM+Plex+Sans+Arabic:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{{--bg:#0E1412;--surface:#151D1A;--ink:#EDEAE0;--muted:#9AA09A;--line:#273129;--accent:#56A896}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{min-height:100vh;background:var(--bg);color:var(--ink);
    font-family:"IBM Plex Sans Arabic",system-ui,sans-serif;
    display:flex;flex-direction:column;align-items:center;justify-content:center;padding:28px 18px}}
  .brand{{margin-bottom:24px}}
  .brand img{{height:30px;width:auto;display:block}}
  .list{{width:100%;max-width:400px;display:flex;flex-direction:column;gap:10px}}
  .person{{display:flex;flex-direction:column;gap:3px;text-decoration:none;color:var(--ink);
    background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 20px}}
  .person:hover{{border-color:var(--accent)}}
  .person strong{{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:1.15rem}}
  .person span{{font-size:.82rem;color:var(--muted)}}
</style>
</head>
<body>
  <div class="brand"><img src="/logo-white.png" alt="Andexa"></div>
  <nav class="list">
{rows}
  </nav>
</body>
</html>
"""


def main() -> None:
    template = (ROOT / "template" / "card.html").read_text(encoding="utf-8")
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    shutil.copy(ROOT / "template" / "qrcode.min.js", SITE / "qrcode.min.js")
    shutil.copy(ROOT / "template" / "logo-white.png", SITE / "logo-white.png")
    shutil.copy(ROOT / "template" / "logo-ink.png", SITE / "logo-ink.png")
    (SITE / "CNAME").write_text(DOMAIN + "\n", encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    entries = []
    for person_dir in sorted(PEOPLE.iterdir()):
        cfg = person_dir / "card.json"
        if not cfg.is_file():
            continue
        slug = person_dir.name
        p = json.loads(cfg.read_text(encoding="utf-8"))
        photo = next(
            (person_dir / n for n in ("photo.jpg", "photo.png")
             if (person_dir / n).is_file()),
            None,
        )
        out = SITE / slug
        out.mkdir()
        (out / "index.html").write_text(
            render_card(template, p, slug, photo is not None),
            encoding="utf-8", newline="\n",
        )
        with open(out / f"{slug}.vcf", "w", encoding="utf-8", newline="") as f:
            f.write(build_vcf(p, photo))
        if photo:
            im = Image.open(photo).convert("RGB")
            im.thumbnail((640, 640), Image.LANCZOS)
            im.save(out / "photo.jpg", "JPEG", quality=88, optimize=True)
        entries.append({"slug": slug, **p})
        print(f"built /{slug}/ (photo: {'yes' if photo else 'no'})")

    (SITE / "index.html").write_text(
        render_directory(entries), encoding="utf-8", newline="\n"
    )
    print(f"done: {len(entries)} card(s) -> site/")


if __name__ == "__main__":
    main()
