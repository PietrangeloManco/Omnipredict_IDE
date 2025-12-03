from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.http import urlencode
from django.shortcuts import render
import csv
from itertools import islice

PER_PAGE_DEFAULT = 100

def _read_csv_page(path, page, per_page):
    """Read only the requested page from a large CSV (no pandas needed)."""
    page = max(int(page or 1), 1)
    per_page = max(int(per_page or PER_PAGE_DEFAULT), 1)

    total_rows = 0
    with open(path, newline="", encoding="utf-8") as f:
        total_rows = sum(1 for _ in f) - 1  # minus header

    start = (page - 1) * per_page
    end = start + per_page

    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        headers = next(r)
        # Skip to start and take per_page rows
        rows = list(islice(islice(r, start, None), per_page))

    num_pages = (total_rows + per_page - 1) // per_page if total_rows > 0 else 1
    return headers, rows, total_rows, page, per_page, num_pages

@staff_member_required
def collected_data_view(request):
    page = request.GET.get("page", "1")
    per_page = request.GET.get("per_page", str(PER_PAGE_DEFAULT))

    headers, rows, total, page, per_page, num_pages = _read_csv_page(
        settings.COLLECTED_DATA_CSV, page, per_page
    )

    # Build page links (stay on same per_page)
    def q(p):
        return "?" + urlencode({"page": p, "per_page": per_page})

    return render(request, "admin/collected_data.html", {
        "title": "Dati Raccolti",
        "headers": headers,
        "rows": rows,
        "total": total,
        "page": page,
        "per_page": per_page,
        "num_pages": num_pages,
        "has_prev": page > 1,
        "has_next": page < num_pages,
        "prev_qs": q(page - 1) if page > 1 else None,
        "next_qs": q(page + 1) if page < num_pages else None,
    })
