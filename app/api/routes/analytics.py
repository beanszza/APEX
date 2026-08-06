"""Analytics API Router for APEX.

Implements /api/analytics/dashboard, /api/analytics/ai, and /api/analytics/compile.
"""

import json
import logging
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis

from app.db.mongo import get_database
from app.db.redis import get_redis_client
from app.schemas.envelope import ApiResponse
from app.models.dashboard import DashboardStatsDocument
from app.models.recommendations import AiRecommendationDocument
from app.services.analytics_compiler import AnalyticsCompilerService
from app.core.auth import get_current_user_claims

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=ApiResponse[DashboardStatsDocument])
async def get_dashboard_stats(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis: Redis = Depends(get_redis_client),
    claims: dict = Depends(get_current_user_claims),
):
    # 1. Check Redis Cache
    try:
        cached = await redis.get("analytics_dashboard_main")
        if cached:
            doc = DashboardStatsDocument.model_validate_json(cached)
            return ApiResponse.success_response(doc, "Dashboard analytics fetched from Redis cache")
    except Exception as ex:
        logger.warning("Redis read error: %s", ex)

    # 2. Fetch from MongoDB
    try:
        doc_dict = await db["DashboardStats"].find_one({"_id": "dashboard_main"})
        if doc_dict:
            doc = DashboardStatsDocument.model_validate(doc_dict)
            await redis.set("analytics_dashboard_main", doc.model_dump_json(by_alias=True), ex=60)
            return ApiResponse.success_response(doc, "Dashboard analytics fetched from MongoDB")
    except Exception as ex:
        logger.warning("MongoDB read error: %s", ex)

    # 3. Live compile fallback from PostgreSQL
    compiler = AnalyticsCompilerService(mongo_db=db, redis_client=redis)
    compiled = await compiler.compile_dashboard_stats()
    return ApiResponse.success_response(compiled, "Dashboard analytics generated live from PostgreSQL Read-Only")


@router.get("/ai", response_model=ApiResponse[AiRecommendationDocument])
async def get_ai_recommendations(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis: Redis = Depends(get_redis_client),
    claims: dict = Depends(get_current_user_claims),
):
    # 1. Check Redis Cache
    try:
        cached = await redis.get("analytics_ai_recommendations")
        if cached:
            doc = AiRecommendationDocument.model_validate_json(cached)
            return ApiResponse.success_response(doc, "AI recommendations fetched from Redis cache")
    except Exception as ex:
        logger.warning("Redis read error: %s", ex)

    # 2. Fetch from MongoDB
    try:
        doc_dict = await db["AiRecommendations"].find_one({"_id": "ai_recommendations"})
        if doc_dict:
            doc = AiRecommendationDocument.model_validate(doc_dict)
            await redis.set("analytics_ai_recommendations", doc.model_dump_json(by_alias=True), ex=60)
            return ApiResponse.success_response(doc, "AI recommendations fetched from MongoDB")
    except Exception as ex:
        logger.warning("MongoDB read error: %s", ex)

    # 3. Live compile fallback from Scikit-Learn Engine
    compiler = AnalyticsCompilerService(mongo_db=db, redis_client=redis)
    compiled = await compiler.compile_ai_recommendations()
    return ApiResponse.success_response(compiled, "AI recommendations generated live from Scikit-Learn Engine")


@router.post("/compile", response_model=ApiResponse[str])
async def trigger_compilation(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis: Redis = Depends(get_redis_client),
    claims: dict = Depends(get_current_user_claims),
):
    compiler = AnalyticsCompilerService(mongo_db=db, redis_client=redis)
    await compiler.compile_all_analytics()
    return ApiResponse.success_response("Phase 2 Analytics successfully compiled to MongoDB and cached in Redis.", "Compilation complete")
