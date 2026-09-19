"""AI Recommendations Pydantic Models for APEX."""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.dashboard import BaseCamelModel


class ProcurementAiRecommendationDto(BaseCamelModel):
    item_id: int
    item_name: str = ""
    current_stock: float = 0.0
    predicted_monthly_usage: float = 0.0
    recommended_reorder_qty: float = 0.0
    confidence: str = "High"
    recommendation_basis: str = ""


class ProductionAiRecommendationDto(BaseCamelModel):
    recipe_id: int
    recipe_name: str = ""
    recommended_batch_count: int = 0
    recommended_output_qty: float = 0.0
    confidence: str = "High"
    recommendation_basis: str = ""


class AiRecommendationDocument(BaseCamelModel):
    id: str = Field(default="ai_recommendations")
    last_compiled_at: datetime = Field(default_factory=datetime.utcnow)
    model_type: str = "Scikit-learn Linear Regression & Demand Velocity Engine"
    procurement_recommendations: list[ProcurementAiRecommendationDto] = Field(default_factory=list)
    production_recommendations: list[ProductionAiRecommendationDto] = Field(default_factory=list)
