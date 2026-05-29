from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["jobs"])

# POST /api/search-jobs              — implemented in Phase 3/4
# GET  /api/jobs/{id}/tailor         — implemented in Phase 4
# GET  /api/jobs/{id}/research       — implemented in Phase 5
