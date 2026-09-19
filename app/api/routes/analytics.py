"""Analytics API Router for APEX.

Implements /api/analytics/dashboard, /api/analytics/ai, and /api/analytics/compile.
"""

import logging
from fastapi import APIRouter, Depends

from app.db.postgres import load_document, save_document, cache_get, cache_set
from app.schemas.envelope import ApiResponse
from app.models.dashboard import DashboardStatsDocument
from app.models.recommendations import AiRecommendationDocument
from app.services.analytics_compiler import AnalyticsCompilerService
from app.core.auth import get_current_user_claims

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=ApiResponse[DashboardStatsDocument])
async def get_dashboard_stats(
    claims: dict = Depends(get_current_user_claims),
):
    # 1. Check in-memory cache
    cached = cache_get("analytics_dashboard_main")
    if cached:
        doc = DashboardStatsDocument.model_validate_json(cached)
        return ApiResponse.success_response(doc, "Dashboard analytics fetched from in-memory cache")

    # 2. Fetch from PostgreSQL analytics_documents
    doc_dict = load_document("dashboard_main")
    if doc_dict:
        doc = DashboardStatsDocument.model_validate(doc_dict)
        cache_set("analytics_dashboard_main", doc.model_dump_json(by_alias=True), ttl_seconds=86400)
        return ApiResponse.success_response(doc, "Dashboard analytics fetched from PostgreSQL")

    # 3. Live compile fallback from PostgreSQL
    compiler = AnalyticsCompilerService()
    compiled = await compiler.compile_dashboard_stats()
    compiled_json = compiled.model_dump_json(by_alias=True)
    try:
        save_document("dashboard_main", compiled_json)
        cache_set("analytics_dashboard_main", compiled_json, ttl_seconds=86400)
    except Exception as ex:
        logger.warning("Failed to persist live compiled dashboard stats: %s", ex)
    return ApiResponse.success_response(compiled, "Dashboard analytics generated live from PostgreSQL Read-Only")


@router.get("/ai", response_model=ApiResponse[AiRecommendationDocument])
async def get_ai_recommendations(
    claims: dict = Depends(get_current_user_claims),
):
    # 1. Check in-memory cache
    cached = cache_get("analytics_ai_recommendations")
    if cached:
        doc = AiRecommendationDocument.model_validate_json(cached)
        return ApiResponse.success_response(doc, "AI recommendations fetched from in-memory cache")

    # 2. Fetch from PostgreSQL analytics_documents
    doc_dict = load_document("ai_recommendations")
    if doc_dict:
        doc = AiRecommendationDocument.model_validate(doc_dict)
        cache_set("analytics_ai_recommendations", doc.model_dump_json(by_alias=True), ttl_seconds=86400)
        return ApiResponse.success_response(doc, "AI recommendations fetched from PostgreSQL")

    # 3. Live compile fallback from Scikit-Learn Engine
    compiler = AnalyticsCompilerService()
    compiled = await compiler.compile_ai_recommendations()
    compiled_json = compiled.model_dump_json(by_alias=True)
    try:
        save_document("ai_recommendations", compiled_json)
        cache_set("analytics_ai_recommendations", compiled_json, ttl_seconds=86400)
    except Exception as ex:
        logger.warning("Failed to persist live compiled AI recommendations: %s", ex)
    return ApiResponse.success_response(compiled, "AI recommendations generated live from Scikit-Learn Engine")


@router.post("/compile", response_model=ApiResponse[str])
async def trigger_compilation(
    claims: dict = Depends(get_current_user_claims),
):
    compiler = AnalyticsCompilerService()
    await compiler.compile_all_analytics()
    return ApiResponse.success_response("Phase 2 Analytics successfully compiled to PostgreSQL and cached in memory.", "Compilation complete")
