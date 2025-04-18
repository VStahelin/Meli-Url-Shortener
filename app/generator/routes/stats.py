import httpx
from fastapi import APIRouter


from app.generator.schema import RouteStats, StandardResponse
from app.settings import PROMETHEUS_URL

router = APIRouter(prefix="/statics", tags=["metrics"])


@router.get("/", response_model=StandardResponse[list[RouteStats]])
async def get_latency_stats():
    """
    Fetches latency and request statistics from Prometheus.

    Queries Prometheus for metrics such as average response time,
    requests per second, total requests in the last minute, and
    total accumulated requests and response times.

    Returns:
        JSONResponse: A list of metrics for each route and method.
    """

    query_sum_rate = (
        "sum(rate(http_request_duration_seconds_sum[1m])) by (handler, method)"
    )
    query_count_rate = (
        "sum(rate(http_request_duration_seconds_count[1m])) by (handler, method)"
    )
    query_total_minute = (
        "sum(increase(http_request_duration_seconds_count[1m])) by (handler, method)"
    )
    query_sum_total = "sum(http_request_duration_seconds_sum) by (handler, method)"
    query_count_total = "sum(http_request_duration_seconds_count) by (handler, method)"

    async with httpx.AsyncClient() as client:
        sum_resp = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query", params={"query": query_sum_rate}
        )
        count_resp = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query", params={"query": query_count_rate}
        )
        total_minute_resp = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query", params={"query": query_total_minute}
        )

        sum_total_resp = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query", params={"query": query_sum_total}
        )
        count_total_resp = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query", params={"query": query_count_total}
        )

    if any(
        r.status_code != 200
        for r in [
            sum_resp,
            count_resp,
            total_minute_resp,
            sum_total_resp,
            count_total_resp,
        ]
    ):

        return {
            "success": False,
            "error": "Failed to query Prometheus",
        }

    # 1m metrics
    sum_data = {
        f"{item['metric']['method']} {item['metric']['handler']}": float(
            item["value"][1]
        )
        for item in sum_resp.json()["data"]["result"]
    }
    count_data = {
        f"{item['metric']['method']} {item['metric']['handler']}": float(
            item["value"][1]
        )
        for item in count_resp.json()["data"]["result"]
    }
    total_minute_data = {
        f"{item['metric']['method']} {item['metric']['handler']}": int(
            float(item["value"][1])
        )
        for item in total_minute_resp.json()["data"]["result"]
    }

    # Totals
    sum_total_data = {
        f"{item['metric']['method']} {item['metric']['handler']}": float(
            item["value"][1]
        )
        for item in sum_total_resp.json()["data"]["result"]
    }
    count_total_data = {
        f"{item['metric']['method']} {item['metric']['handler']}": int(
            float(item["value"][1])
        )
        for item in count_total_resp.json()["data"]["result"]
    }

    response = []
    all_keys = set(sum_total_data) | set(count_total_data)

    for key in all_keys:
        rate_sum = sum_data.get(key, 0)
        rate_count = count_data.get(key, 0)
        total_minute = total_minute_data.get(key, 0)

        avg_ms = (rate_sum / rate_count) * 1000 if rate_count else 0

        total_sum_ms = sum_total_data.get(key, 0.0) * 1000
        total_count = count_total_data.get(key, 0)

        response.append(
            {
                "route": key,
                "avg_response_time_ms": round(avg_ms, 3),
                "requests_per_second": round(rate_count, 2),
                "total_requests_last_minute": total_minute,
                "total_requests": total_count,
                "total_response_time_ms": round(total_sum_ms, 2),
            }
        )

    return {"success": True, "data": response}
