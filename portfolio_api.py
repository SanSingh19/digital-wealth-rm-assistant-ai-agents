import requests

BASE_URL = "http://localhost:8080"


class PortfolioApi:

    @staticmethod
    def get_portfolio(client_id):

        response = requests.get(
            f"{BASE_URL}/client/portfolio",
            params={
                "clientId": client_id
            }
        )

        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_performance(client_id, rm_id):

        response = requests.get(
            f"{BASE_URL}/client/performance-months",
            params={
                "clientId": client_id,
                "rmId": rm_id
            }
        )

        response.raise_for_status()
        return response.json()