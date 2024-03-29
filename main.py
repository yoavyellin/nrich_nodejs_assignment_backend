import json
import redis
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import os
from deps_graph_class import DependenciesGraph
from get_deps import get_deps
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

redis_db = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    password=os.getenv("REDIS_PASSWORD"),
)

CACHE_REVALIDATE = 3600  # 1 hour


@app.get("/{package_name}")
def main(package_name: str, response: Response):

    # First check for cached response
    cache = redis_db.get(package_name)
    if cache:
        print("Cache hit")
        return {"data": json.loads(cache.decode("utf-8"))}

    else:
        print("Cache miss")

        # Check if package_name exists and return 404 if not
        if not package_exist(package_name):
            response.status_code = 404
            return {"error": f'"{package_name}" does not exist.'}

        # If package_name does exist, generate its graph and return the data
        # in the correct format for vis.js (graph package) in the frontend.
        try:
            deps_graph = DependenciesGraph(package_name)
            deps_graph.generate_graph()

            generated_deps_graph = {
                "edges": deps_graph.edges,
                "nodes": deps_graph.nodes,
            }

            redis_db.setex(
                package_name, CACHE_REVALIDATE, json.dumps(generated_deps_graph)
            )  # Cache response
            return {"data": generated_deps_graph}

        except Exception as e:
            print("An error occurred:", e)
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"error": f"An internal error occurred: {str(e)}"}


def package_exist(package_name):
    try:
        res = get_deps(package_name)

        if len(res) >= 0:
            return True
        else:
            return False

    except Exception as e:
        print(e)
        return False
