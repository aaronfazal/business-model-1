#!/usr/bin/env python3
"""Build a client's one-page website from their site.json.

Usage:
    python3 build.py clients/<client-folder>            # builds clients/<client-folder>/dist/
    python3 build.py clients/<client-folder> --preview  # also writes preview.html with images embedded

The dist/ folder is what gets uploaded to hosting (GitHub Pages, Netlify, etc.).
"""
import base64
import datetime
import html
import json
import mimetypes
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote_plus

HERE = Path(__file__).resolve().parent


def esc(value):
    return html.escape(str(value), quote=True)


def phone_link(phone):
    digits = re.sub(r"[^\d+]", "", phone)
    if digits.startswith("0"):
        digits = "+44" + digits[1:]
    return digits


def build_sections(cfg):
    services = "\n".join(
        "        <li><h3>{}</h3><p>{}</p>{}</li>".format(
            esc(s["name"]),
            esc(s["description"]),
            '<span class="from">From {}</span>'.format(esc(s["from_price"])) if s.get("from_price") else "",
        )
        for s in cfg["services"]
    )

    gallery = "\n".join(
        '        <figure><img src="images/{}" alt="{}" loading="lazy" width="600" height="600"><figcaption>{}</figcaption></figure>'.format(
            esc(g["file"]), esc(g["caption"]), esc(g["caption"])
        )
        for g in cfg["gallery"]
    )

    def stars(n):
        n = int(round(float(n)))
        icons = '<svg aria-hidden="true"><use href="#i-star"/></svg>' * n
        return '<span class="stars" role="img" aria-label="{} out of 5 stars">{}</span>'.format(n, icons)

    reviews = "\n".join(
        "        <blockquote>{}<p>{}</p><cite>{}{}</cite></blockquote>".format(
            stars(r.get("stars", 5)),
            esc(r["text"]), esc(r["name"]), ", " + esc(r["location"]) if r.get("location") else ""
        )
        for r in cfg["reviews"]
    )

    trust_points = "\n".join(
        '        <li><svg class="icon" aria-hidden="true"><use href="#i-check"/></svg>{}</li>'.format(esc(t))
        for t in cfg.get("trust_points", [])
    )

    if cfg.get("map_query"):
        map_html = (
            '      <div class="map"><iframe title="Map of the area we cover around {}" '
            'src="https://www.google.com/maps?q={}&amp;output=embed" loading="lazy" '
            'referrerpolicy="no-referrer-when-downgrade"></iframe></div>'
        ).format(esc(cfg["town"]), quote_plus(cfg["map_query"]))
    else:
        map_html = ""

    if cfg.get("google_reviews_url"):
        reviews_link = '      <a class="reviews-link" href="{}">Read all our reviews on Google</a>'.format(
            esc(cfg["google_reviews_url"])
        )
    else:
        reviews_link = ""

    steps = "\n".join(
        "        <li><h3>{}</h3><p>{}</p></li>".format(esc(s["title"]), esc(s["text"]))
        for s in cfg["steps"]
    )

    areas = "\n".join("        <li>{}</li>".format(esc(a)) for a in cfg["areas"])
    job_options = "\n".join("            <option>{}</option>".format(esc(s["name"])) for s in cfg["services"])

    links = []
    if cfg.get("checkatrade_url"):
        links.append('<a href="{}">Checkatrade profile</a>'.format(esc(cfg["checkatrade_url"])))
    if cfg.get("facebook_url"):
        links.append('<a href="{}">Facebook</a>'.format(esc(cfg["facebook_url"])))
    if cfg.get("instagram_url"):
        links.append('<a href="{}">Instagram</a>'.format(esc(cfg["instagram_url"])))
    footer_links = "      <p>{}</p>".format(" · ".join(links)) if links else ""

    if cfg.get("form_endpoint"):
        form_attrs = 'action="{}" method="POST"'.format(esc(cfg["form_endpoint"]))
    else:
        form_attrs = 'action="mailto:{}" method="POST" enctype="text/plain"'.format(esc(cfg["email"]))

    rating = cfg.get("review_rating")
    count = cfg.get("review_count")
    if rating and count:
        rating_block = '      <p class="rating">{}<span>{} from {} Google reviews</span></p>'.format(
            stars(rating), esc(rating), esc(count)
        )
        review_intro = "Rated {} out of 5 by customers on Google.".format(rating)
    else:
        rating_block = ""
        review_intro = "Reviews from recent customers."

    schema = {
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "name": cfg["business_name"],
        "telephone": phone_link(cfg["phone"]),
        "email": cfg["email"],
        "address": {"@type": "PostalAddress", "streetAddress": cfg["address"], "addressCountry": "GB"},
        "areaServed": cfg["areas"],
    }
    if cfg.get("site_url"):
        schema["url"] = cfg["site_url"]
    if rating and count:
        schema["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": rating, "reviewCount": count}

    return {
        "title": cfg.get("title") or "{} | Carpenters in {}".format(cfg["business_name"], cfg["town"]),
        "meta_description": cfg["meta_description"],
        "css": (HERE / "styles.css").read_text(),
        "schema": json.dumps(schema, indent=2),
        "business_name": esc(cfg["business_name"]),
        "legal_name": esc(cfg.get("legal_name") or cfg["business_name"]),
        "phone": esc(cfg["phone"]),
        "phone_link": esc(phone_link(cfg["phone"])),
        "email": esc(cfg["email"]),
        "address": esc(cfg["address"]),
        "headline": esc(cfg["headline"]),
        "intro": esc(cfg["intro"]),
        "hero_image": "images/" + esc(cfg["hero_image"]["file"]),
        "hero_alt": esc(cfg["hero_image"]["alt"]),
        "area_line": esc(cfg["area_line"]),
        "services_intro": esc(cfg["services_intro"]),
        "services": services,
        "gallery": gallery,
        "rating_block": rating_block,
        "trust_points": trust_points,
        "review_intro": esc(review_intro),
        "reviews": reviews,
        "reviews_link": reviews_link,
        "map": map_html,
        "steps": steps,
        "area_intro": esc(cfg["area_intro"]),
        "areas": areas,
        "reply_time": esc(cfg.get("reply_time", "one working day")),
        "job_options": job_options,
        "form_attrs": form_attrs,
        "footer_links": footer_links,
        "year": str(datetime.date.today().year),
    }


def check(cfg):
    warnings = []
    for r in cfg["reviews"]:
        if r["name"].lower().startswith("sample"):
            warnings.append("Sample review still in place: replace with a real customer review before launch.")
            break
    if not cfg.get("form_endpoint"):
        warnings.append("No form_endpoint set: the quote form will fall back to opening the visitor's email app.")
    for g in cfg["gallery"]:
        if g["file"].startswith("placeholder"):
            warnings.append("Placeholder photos still in place: swap in the client's own work photos.")
            break
    return warnings


def embed_images(page, images_dir):
    def repl(match):
        path = images_dir / match.group(1)
        if not path.exists():
            return match.group(0)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = base64.b64encode(path.read_bytes()).decode()
        return 'src="data:{};base64,{}"'.format(mime, data)

    return re.sub(r'src="images/([^"]+)"', repl, page)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    client_dir = Path(sys.argv[1]).resolve()
    cfg = json.loads((client_dir / "site.json").read_text())
    tokens = build_sections(cfg)

    page = (HERE / "template.html").read_text()
    for key, value in tokens.items():
        page = page.replace("{{" + key + "}}", value)
    leftover = re.findall(r"{{\w+}}", page)
    if leftover:
        sys.exit("Unfilled placeholders: " + ", ".join(sorted(set(leftover))))

    dist = client_dir / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    (dist / "images").mkdir(parents=True)
    (dist / "index.html").write_text(page)
    for img in (client_dir / "images").iterdir():
        shutil.copy(img, dist / "images" / img.name)

    if "--preview" in sys.argv:
        (client_dir / "preview.html").write_text(embed_images(page, client_dir / "images"))

    print("Built", dist / "index.html")
    for w in check(cfg):
        print("  ! " + w)


if __name__ == "__main__":
    main()
