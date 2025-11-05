"""
Prometheus metrics dla workflow monitoring.

Metryki:
- workflow_executions_total: Licznik wykonanych workflow
- workflow_execution_errors_total: Licznik błędów wykonania
- workflow_validations_total: Licznik walidacji
- workflow_execution_duration_seconds: Histogram czasu wykonania
- workflow_validation_duration_seconds: Histogram czasu walidacji
- node_execution_duration_seconds: Histogram czasu wykonania node'a
- workflow_executions_running: Gauge aktualnie wykonywanych workflow
- workflow_executions_pending: Gauge oczekujących wykonań w kolejce
"""

from prometheus_client import Counter, Histogram, Gauge

# =============================================================================
# Counters (monotoniczne liczniki)
# =============================================================================

workflow_executions_total = Counter(
    'workflow_executions_total',
    'Łączna liczba wykonań workflow',
    ['status', 'workflow_name']
)

workflow_execution_errors_total = Counter(
    'workflow_execution_errors_total',
    'Łączna liczba błędów wykonania workflow',
    ['workflow_name', 'error_type']
)

workflow_validations_total = Counter(
    'workflow_validations_total',
    'Łączna liczba walidacji workflow',
    ['is_valid']
)

# =============================================================================
# Histograms (rozkłady czasowe)
# =============================================================================

workflow_execution_duration_seconds = Histogram(
    'workflow_execution_duration_seconds',
    'Czas wykonania workflow w sekundach',
    ['workflow_name', 'node_count'],
    buckets=(5, 10, 30, 60, 120, 300, 600)  # 5s do 10min
)

workflow_validation_duration_seconds = Histogram(
    'workflow_validation_duration_seconds',
    'Czas walidacji workflow w sekundach',
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

node_execution_duration_seconds = Histogram(
    'node_execution_duration_seconds',
    'Czas wykonania pojedynczego node\'a w sekundach',
    ['node_type'],
    buckets=(0.5, 1, 5, 10, 30, 60, 120)
)

# =============================================================================
# Gauges (wartości aktualne)
# =============================================================================

workflow_executions_running = Gauge(
    'workflow_executions_running',
    'Liczba aktualnie wykonywanych workflow'
)

workflow_executions_pending = Gauge(
    'workflow_executions_pending',
    'Liczba oczekujących wykonań workflow w kolejce'
)
