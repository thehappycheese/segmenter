from typing import Any, Optional, Dict
import requests
import urllib
import math
import pandas as pd
from deprecated import deprecated


DATA_SOURCE_URL = "https://mrgis.mainroads.wa.gov.au/arcgis/rest/services/OpenData/RoadAssets_DataPortal/MapServer/17/query"


@deprecated(reason="This function has been moved to another package. See https://github.com/thehappycheese/fetchopendata", version="0.5.1")
def fetch_road_network_info(
    url:str=DATA_SOURCE_URL,
    chunk_limit:Optional[int]=None,
    **kwargs
    ) -> Dict[str, Any]:

    query_params = {
        "where":"1=1",
        "outFields":",".join({"ROAD", "START_SLK", "END_SLK", "CWY", "NETWORK_TYPE", "START_TRUE_DIST", "END_TRUE_DIST", "RA_NO"}),
        "outSR":4326,
        "f":"json",
        "returnGeometry":False,
        **kwargs
    }

    response = requests.request("GET", f"{url}?"+urllib.parse.urlencode(query_params | {"returnCountOnly":True}))
    record_count = response.json()["count"]

    print(f"Downloading {record_count} records" + (":" if chunk_limit is None else f", chunk_limit={chunk_limit}:"))

    ASSUMED_CHUNK_SIZE = 1000
    if chunk_limit is not None:
        print("." * min(chunk_limit, math.floor(record_count/ASSUMED_CHUNK_SIZE)))
    else:
        print("." * math.floor(record_count/ASSUMED_CHUNK_SIZE))

    output=[]
    offset = 0
    chunk_counter = 0

    while True:

        if chunk_limit is not None and chunk_counter >= chunk_limit:
            break

        chunk_counter += 1

        response = requests.request(
            "GET",
             f"{url}?"
            + urllib.parse.urlencode(
                {"resultOffset":offset} | query_params
            )
        )

        json = response.json()
        
        offset += len(json["features"])
        output.extend(json["features"])

        if "exceededTransferLimit" not in json or not json["exceededTransferLimit"]:
            break
        print(".", end="")

    print(f"\nDownload Completed. received {len(output)} records")
    json["features"] = output

    result = pd.json_normalize(json, record_path="features")
    result.columns = [c.replace("attributes.", "") for c in result.columns]

    return result