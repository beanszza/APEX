# APEX API Endpoint Documentation

## Base URL

- **Development Direct**: `http://localhost:5011`
- **Via Gateway**: `http://localhost:5001/api/scms-analytics`

---

## Health Check

### `GET /health`

Checks service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "APEX Analytics Engine"
}
```

---

## Analytics Endpoints

### 1. Dashboard Stats

`GET /api/analytics/dashboard`

Returns compiled KPIs, inventory category distribution, procurement trends, production yield, stock alerts, frequently produced items, and branch delivery volumes.

**Query Flow:**
1. Checks Redis cache (`analytics_dashboard_main`).
2. If cache miss, checks MongoDB (`apex_db.DashboardStats`).
3. If Mongo miss, computes live from PostgreSQL (`scm_db`) using Pandas.

**Response Envelope:**
```json
{
  "success": true,
  "message": "Dashboard analytics fetched from Redis cache",
  "data": {
    "id": "dashboard_main",
    "lastCompiledAt": "2026-08-06T23:15:00.000Z",
    "kpis": {
      "totalActiveItems": 42,
      "lowStockCount": 3,
      "totalBatchesThisMonth": 18,
      "overallProductionYieldPercent": 98.5,
      "activeSupplierCount": 8,
      "pendingPurchaseOrders": 4,
      "totalStockTransfersThisMonth": 12
    },
    "inventoryChart": [
      { "category": "Raw Materials", "itemCount": 24 },
      { "category": "Tools and Supplies", "itemCount": 18 }
    ],
    "procurementChart": [
      { "month": "Aug 2026", "totalOrdersCount": 5, "totalQtyOrdered": 450.0 }
    ],
    "productionChart": {
      "totalBatches": 20,
      "successfulBatches": 19,
      "failedBatches": 1,
      "yieldSuccessRate": 95.0
    },
    "lowStockAlerts": [
      {
        "itemId": 1,
        "itemName": "Flour 25kg",
        "currentStock": 2.0,
        "minStockLevel": 10.0,
        "urgency": "WARNING"
      }
    ],
    "frequentlyProducedProducts": [
      { "recipeName": "Pancake Mix", "batchCount": 8, "totalOutputQty": 800.0 }
    ],
    "branchDeliveries": [
      { "branchName": "Branch 1 - Quezon City", "deliveryCount": 7, "totalItemsTransferred": 350.0 }
    ]
  }
}
```

---

### 2. AI Recommendations

`GET /api/analytics/ai`

Returns Scikit-Learn predictive recommendations for procurement reordering and production planning.

**Response Envelope:**
```json
{
  "success": true,
  "message": "AI recommendations fetched from MongoDB",
  "data": {
    "id": "ai_recommendations",
    "lastCompiledAt": "2026-08-06T23:15:00.000Z",
    "modelType": "Scikit-Learn Linear Regression & Demand Velocity Engine",
    "procurementRecommendations": [
      {
        "itemId": 1,
        "itemName": "Flour 25kg",
        "currentStock": 2.0,
        "predictedMonthlyUsage": 28.5,
        "recommendedReorderQty": 98.0,
        "confidence": "High",
        "recommendationBasis": "Scikit-Learn regression predicts 28.5 units monthly demand based on historical velocity."
      }
    ],
    "productionRecommendations": [
      {
        "recipeId": 3,
        "recipeName": "Pancake Mix Batch",
        "recommendedBatchCount": 4,
        "recommendedOutputQty": 400.0,
        "confidence": "High",
        "recommendationBasis": "Scikit-Learn demand forecasting suggests 4 batches to fulfill projected branch demand."
      }
    ]
  }
}
```

---

### 3. Trigger Analytics Compilation

`POST /api/analytics/compile`

Triggers a manual refresh of PostgreSQL read-only data, runs Pandas calculations & Scikit-Learn predictions, and updates MongoDB and Redis.

**Response Envelope:**
```json
{
  "success": true,
  "message": "Phase 2 Analytics successfully compiled to MongoDB and cached in Redis.",
  "data": "Compilation complete"
}
```
