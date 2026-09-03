from varne.providers.base import ProviderClient


class JsonPlaceholderClient(ProviderClient):
    @property
    def base_url(self) -> str:
        return "https://jsonplaceholder.typicode.com"

    def fetch_posts(self) -> str:
        response = self.http.get(f"{self.base_url}/posts")

        response.raise_for_status()

        return response.text
