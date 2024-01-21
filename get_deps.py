import requests
from requests.exceptions import HTTPError


def get_deps(package_name):
    """
    Returns a list of all the dependencies of package_name.
    """

    url = f"https://registry.npmjs.org/{package_name}/latest"

    try:
        response = requests.get(url)
        response.raise_for_status()  # This will raise an HTTPError if the status is 4xx or 5xx
        data = response.json()
        return list(
            data.get("dependencies", {}).keys()
        )  # Returns a list of the keys in the dictionary

    except HTTPError as http_err:
        if response.status_code == 404:
            raise ValueError(f"Package '{package_name}' does not exist.") from http_err
        else:
            raise ValueError(
                f"Error fetching dependencies for '{package_name}': {http_err}"
            ) from http_err

    except Exception as err:
        raise ValueError(f"An unexpected error occurred: {err}") from err
