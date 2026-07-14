"""
STATUS: REAL — OLAP Analytics & CQRS Data Lake for AsimNexus
ASIMNEXUS Analytics Module
==========================
CQRS (Command Query Responsibility Segregation) Data Lake:
- Write path: VectorMemory (core/vectormemory.py)
- Read/OLAP path: DataLake (this module)

Reference: Digital Twin Architecture (Graeme Wright),
           CQRS Pattern (Martin Fowler),
           OLAP Cube Design (Ralph Kimball)

Features:
  - OLAP-style analytics over VectorMemory snapshots
  - Materialized views for common queries
  - Time-series aggregation (hourly, daily, weekly, monthly)
  - Read-optimized query interface (CQRS read side)
  - Integration with Mirror Module for self-evolution
  - Export to structured formats for fine-tuning
"""

from .data_lake import (
    DataLake,
    DataLakeSnapshot,
    MaterializedView,
    TimeSeriesAggregation,
    QueryResult,
    get_data_lake,
    reset_data_lake,
)

__all__ = [
    "DataLake",
    "DataLakeSnapshot",
    "MaterializedView",
    "TimeSeriesAggregation",
    "QueryResult",
    "get_data_lake",
    "reset_data_lake",
]
