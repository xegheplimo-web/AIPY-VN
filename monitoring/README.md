# Monitoring Setup

This directory contains the configuration for monitoring the VietStore API with Prometheus and Grafana.

## Components

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards

## Quick Start

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana
# URL: http://localhost:3001
# Username: admin
# Password: admin

# Access Prometheus
# URL: http://localhost:9090
```

## Dashboards

The VietStore API dashboard includes:

- HTTP Requests Rate
- Request Duration
- HTTP Requests by Status
- Orders Created

## Metrics

The API exposes metrics at `/metrics` endpoint:

- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request duration
- `orders_created_total`: Total orders created
- `payments_processed_total`: Total payments processed
- `users_registered_total`: Total users registered
- `active_users`: Number of active users
- `db_connections_active`: Active database connections
- `db_connections_idle`: Idle database connections
- `cache_hits_total`: Cache hits
- `cache_misses_total`: Cache misses

## Configuration

- Prometheus config: `monitoring/prometheus/prometheus.yml`
- Grafana datasources: `monitoring/grafana/datasources/`
- Grafana dashboards: `monitoring/grafana/dashboards/`

## Customization

To add custom metrics, modify the `prometheus_metrics.py` file in the API server.

To add custom dashboards, create new JSON files in `monitoring/grafana/dashboards/`.
