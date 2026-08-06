"""Dashboard Pydantic Models for APEX."""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


def to_camel(string: str) -> str:
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class BaseCamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class DashboardKpiDto(BaseCamelModel):
    total_active_items: int = 0
    low_stock_count: int = 0
    total_batches_this_month: int = 0
    overall_production_yield_percent: float = 100.0
    active_supplier_count: int = 0
    pending_purchase_orders: int = 0
    total_stock_transfers_this_month: int = 0


class CategoryStockDto(BaseCamelModel):
    category: str = ""
    item_count: int = 0


class MonthlyProcurementDto(BaseCamelModel):
    month: str = ""
    total_orders_count: int = 0
    total_qty_ordered: float = 0.0


class ProductionChartDto(BaseCamelModel):
    total_batches: int = 0
    successful_batches: int = 0
    failed_batches: int = 0
    yield_success_rate: float = 100.0


class SupplierPerformanceChartDto(BaseCamelModel):
    supplier_name: str = ""
    average_lead_time_days: float = 0.0
    total_orders_placed: int = 0


class BranchTransferChartDto(BaseCamelModel):
    branch_name: str = ""
    total_transfers: int = 0
    average_transit_hours: float = 0.0


class LowStockAlertDto(BaseCamelModel):
    item_id: int
    item_name: str = ""
    current_stock: float = 0
    min_stock_level: float = 0
    urgency: str = "WARNING"


class ProductProductionFrequencyDto(BaseCamelModel):
    recipe_name: str = ""
    batch_count: int = 0
    total_output_qty: float = 0.0


class BranchDeliveryVolumeDto(BaseCamelModel):
    branch_name: str = ""
    delivery_count: int = 0
    total_items_transferred: float = 0.0


class DashboardStatsDocument(BaseCamelModel):
    id: str = Field(default="dashboard_main", alias="_id")
    last_compiled_at: datetime = Field(default_factory=datetime.utcnow)
    kpis: DashboardKpiDto = Field(default_factory=DashboardKpiDto)
    inventory_chart: list[CategoryStockDto] = Field(default_factory=list)
    procurement_chart: list[MonthlyProcurementDto] = Field(default_factory=list)
    production_chart: ProductionChartDto = Field(default_factory=ProductionChartDto)
    supplier_chart: list[SupplierPerformanceChartDto] = Field(default_factory=list)
    distribution_chart: list[BranchTransferChartDto] = Field(default_factory=list)
    low_stock_alerts: list[LowStockAlertDto] = Field(default_factory=list)
    frequently_produced_products: list[ProductProductionFrequencyDto] = Field(default_factory=list)
    branch_deliveries: list[BranchDeliveryVolumeDto] = Field(default_factory=list)
