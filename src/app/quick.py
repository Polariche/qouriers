from fastapi import FastAPI, HTTPException
from typing import Union, Dict, List
from collections import deque
import requests
import redis
import json

from lib.models import *
from lib.utils import kube_get_keyspace

app = FastAPI()
app.keyspace = kube_get_keyspace()

@app.post("/query/{query}")
def post_query(query: str, params: Dict):
    try:
        q = app.queries[query]
        method = q.method
    except:
        raise HTTPException(status_code=404, detail=f"Query not found")

    try:
        req = q.apply(params)
    except KeyError as e: 
        raise HTTPException(status_code=422, detail=f"Following variables must be defined: {e.args[0]}")
    
    response = send_to_caller([req])[0]
    
    try:
        body = response.json()['body']
    except KeyError:
        raise HTTPException(status_code=response.status_code, detail=f"Got an error message : {response.json()['detail']}")
    
    result = q.get_result(body, data=params)

    return result

@app.get("/apiqueries")
def available_API_queries():
    # fetch and update queries
    app.queries = get_all_queries()
    return app.queries

@app.get("/ready")
def ready():
    try:
        requests.get(f'http://qourier-caller-{app.keyspace}:80')
    except:
        raise HTTPException(status_code=500, detail=f"No API Callers are available. Please try again.")

    return "ready"

@app.get("/metrics")
def metrics():
    return {}
