import json
import redis
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
import requests
from requests.exceptions import HTTPError
from mangum import Mangum
import os

app = FastAPI()
handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

r = redis.Redis(
    host=os.environ.get("REDIS_HOST",""),
    port=os.environ.get("REDIS_PORT",""),
    password=os.environ.get("REDIS_PASSWORD",""),
)

CACHE_REVALIDATE = 3600  # 1 hour


@app.get("/{package_name}")
def main(package_name: str, response: Response):
    """
    Caching requests using redis DB.
    Recursively building the dependency tree for package_name.

    :return:
        Status 200 - Success
        Status 400 - If the request to npm for package_name fails
        Status 404 - If package_name does not exist in npm
        Status 500 - Other errors
    """
    cache = r.get(package_name)

    if cache:
        print("Cache hit")
        return {"data": json.loads(cache.decode("utf-8"))}

    else:
        print("Cache miss")
        try:
            generated_deps_tree, status_code = generate_deps_tree(
                package_name, is_root=True
            )
            if status_code == status.HTTP_200_OK:
                r.setex(package_name, CACHE_REVALIDATE, json.dumps(generated_deps_tree))
                return {"data": generated_deps_tree}
            else:
                response.status_code = status_code
                return generated_deps_tree  # This will look like this: {"error": <error-message>}

        except Exception as e:
            print("An error occurred:", e)
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"error": f"An internal error occurred: {str(e)}"}


def generate_deps_tree(package_name, is_root=False):
    """
    Generate a dependency tree for a given npm package.

    :param package_name: Name of the npm package.
    :param is_root: Flag to indicate if the package is the root package.
    :return: Dependency tree and status code.
    """
    try:
        deps = get_package_deps(package_name)
    except ValueError as e:
        error_message = str(e)
        status_code = status.HTTP_404_NOT_FOUND if is_root else status.HTTP_400_BAD_REQUEST
        return {"error": error_message} if is_root else {"name": package_name, "children": [{"name": error_message}]}, status_code

    children = []
    for dep_name in deps:
        subtree, _ = generate_deps_tree(dep_name)
        children.append(subtree)

    return {"name": package_name, "children": children}, status.HTTP_200_OK


def get_package_deps(package_name):
    """
    :param package_name: A name of a npm package
    :return: An object with all the dependencies of package_name
    """
    url = f"https://registry.npmjs.org/{package_name}/latest"

    try:
        response = requests.get(url)
        response.raise_for_status()  # This will raise an HTTPError if the status is 4xx or 5xx
        data = response.json()
        return data.get(
            "dependencies", {}
        )  # Returns an empty dict if no dependencies are found

    except HTTPError as http_err:
        if response.status_code == 404:
            raise ValueError(f"Package '{package_name}' does not exist.") from http_err
        else:
            raise ValueError(
                f"Error fetching dependencies for '{package_name}': {http_err}"
            ) from http_err

    except Exception as err:
        raise ValueError(f"An unexpected error occurred: {err}") from err
