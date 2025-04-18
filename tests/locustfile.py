from locust import HttpUser, task, between
import random


class WebsiteUser(HttpUser):
    wait_time = between(0.9, 1.1)
    """
    locust -f locustfile.py --headless -u 1000 -r 100 --host http://localhost:8000 --run-time 1m --csv locust_rps1000
    """

    # Update with some urls(pre created) to randomize
    endpoints = [
        "/_RJDQLde",
        "/YjIgCmZX",
        "/gKGb_DLZ",
    ]

    @task(10)
    def access_random_endpoint(self):
        endpoint = random.choice(self.endpoints)
        with self.client.get(
            endpoint, allow_redirects=False, name="GET no-redirect", catch_response=True
        ) as response:
            if response.status_code != 302:
                response.failure(f"Expected 302, got {response.status_code}")
