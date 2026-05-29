import httpx

pdf = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\ntrailer<</Size 4/Root 1 0 R>>\nstartxref 0\n%%EOF"
)

r = httpx.post(
    "http://127.0.0.1:8000/api/upload-resume",
    files={"file": ("resume.pdf", pdf, "application/pdf")},
    data={"job_title": ""},
    timeout=30,
)
print("Status :", r.status_code)
print("CT     :", r.headers.get("content-type", ""))
print("Body   :", r.text[:300])
