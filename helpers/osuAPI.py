from __future__ import annotations

import aiohttp
import socket
from main import Config

from pydantic import BaseModel
from datetime import datetime
from typing import List, Union

from statistics import StatisticsError, mode

config = Config.getMainInstance()

BASEURL = "https://osu.ppy.sh/api/v2"
GRANTURL = "https://osu.ppy.sh/oauth/token"
CLIENTSECRET = config.osusecret
CLIENTID = config.clientid

accessToken = None

class NestedBeatmap(BaseModel):
    starRating: float

class ApiResponse(BaseModel):
    beatmapsetId: int
    
    title: str
    artist: str
    mapper: str
    
    status: int
    
    submittedDate: datetime
    statusChangedDate: Union[datetime, None] # in-built type union does not work here
    
    mostCommonMode: str
    
    beatmaps: List[NestedBeatmap]
    

async def authenticate():
    print("[API][INFO] Trying to authenticate...")
    
    try:
        connector = aiohttp.TCPConnector(family = socket.AF_INET)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        async with aiohttp.ClientSession(connector = connector, headers = headers) as session:
            try:
                response = await session.post(url = GRANTURL, data = f"client_id={CLIENTID}&client_secret={CLIENTSECRET}&grant_type=client_credentials&scope=public")
                
                global accessToken
                json = await response.json()
                accessToken = json["access_token"]
                
                print("[API][INFO] Successfully authenticated")
                return json["access_token"]
                
            except Exception as e:
                print(f"[API][ERROR] Something went wrong while accessing the osu!API\n{e}")
        
    except aiohttp.ClientError as e:
        print(f"[AIOHTTP][ERROR] Something went wrong with the client\n{e}")
        return None
    
async def mostCommonMode(modes: List[str]):
    try:
        result = mode(modes)
        
        if result == "osu":
            return "standard"
        elif result == "fruits":
            return "catch"
        else:
            return result
    except StatisticsError:
        # Something went wrong so just assume osu!std 
        #TODO change this to display on the embed as none
        return "standard"

async def dataMapper(mode: int, json: dict) -> Union[List[ApiResponse], ApiResponse]:
    """
    Map JSON data to ApiResponse object(s).

    Args:
        mode (int): The mode of data mapping.
            1 (int): Maps a beatmap from a list of beatmapsets and inserts into a list.
                    Endpoint: /api/v2/beatmapsets/search?nsfw=true&s=qualified
                    Returns a list of ApiResponse objects.
            2 (int): Maps a singular beatmap.
                    Endpoint: /api/v2/beatmapsets/{id}
                    Returns a single ApiResponse object.

        json (dict): The JSON data to be mapped.

    Returns:
        Union[List[ApiResponse], ApiResponse]: Depending on the mode:
            - If mode is 1, returns a list of ApiResponse objects.
            - If mode is 2, returns a single ApiResponse object.
    """
    if mode == 1:
        mappedDataList: List[ApiResponse] = []
        for beatmapset in json:
            nested = []
            for beatmap in beatmapset["beatmaps"]:
                nest = NestedBeatmap(
                    starRating = beatmap["difficulty_rating"]
                )
                nested.append(nest)

            modes: List[str] = [beatmap["mode"] for beatmap in beatmapset["beatmaps"]]
             
            mappedData = ApiResponse(
                beatmapsetId = beatmapset["id"],
                title = beatmapset["title"],
                artist = beatmapset["artist"],
                mapper = beatmapset["creator"],
                status = beatmapset["ranked"],
                submittedDate = beatmapset["submitted_date"],
                statusChangedDate = beatmapset["ranked_date"],
                mostCommonMode = await mostCommonMode(modes),
                beatmaps = nested
            )
            mappedDataList.append(mappedData)
        return mappedDataList
    elif mode == 2:
        nested = []
        for beatmap in json["beatmaps"]:
            nest = NestedBeatmap(
                starRating = beatmap["difficulty_rating"]
            )
            nested.append(nest)
        
        modes: List[str] = [beatmap["mode"] for beatmap in json["beatmaps"]]
        
        mappedData = ApiResponse(
            beatmapsetId = json["id"],
            title = json["title"],
            artist = json["artist"],
            mapper = json["creator"],
            status = json["ranked"],
            submittedDate = json["submitted_date"],
            statusChangedDate = json["ranked_date"],
            mostCommonMode = await mostCommonMode(modes),
            beatmaps = nested
        )
        return mappedData
    else:
        raise ValueError("Invalid mode. Mode must be 1 or 2")

async def getBeatmap(id: int) -> ApiResponse | None:
    print("[API][INFO] Trying to get beatmap information...")
    
    try:
        connector = aiohttp.TCPConnector(family = socket.AF_INET)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {accessToken}"
        }
        
        async with aiohttp.ClientSession(connector = connector, headers = headers) as session:
            try:
                response = await session.get(url = f"{BASEURL}/beatmapsets/{id}")
                
                if response.status == 200:
                    print("[API][INFO] Successfully got beatmap data")
                    data = await response.json()
                    
                    mappedData = await dataMapper(2, data)
                    if isinstance(mappedData, ApiResponse):
                        return mappedData
                    else:
                        # This should quite literally never return None from here but its so my linter shuts up
                        return None
                if response.status == 401:
                    print("[API][WARN] HTTP 401, Reauthenticating")
                    await authenticate()
                    print("[API][INFO] Retrying beatmap data fetch")
                    return await getBeatmap(id)
            except Exception as e:
                print(f"[API][ERROR] Something went wrong while fetching beatmap information\n{e}")
                return None

    except aiohttp.ClientError as e:
        print(f"[AIOHTTP][ERROR] Something went wrong with the client\n{e}")
        return None

async def populateDatabase():
    async def getMaps(cursorString = None):
        try:
            connector = aiohttp.TCPConnector(family = socket.AF_INET)
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {accessToken}"
            }
            async with aiohttp.ClientSession(connector = connector, headers = headers) as session:
                response = await session.get(url = f"{BASEURL}/beatmapsets/search?nsfw=true&s=qualified&cursor_string={cursorString}")
                
                if response.status == 200:
                    print("[API][INFO] Successfully got beatmap json")
                    json = await response.json()
                    
                    # This can't be imported at the top of file because of circular imports
                    from helpers.database import insertBeatmapsetData

                    # This is of type List[ApiResponse]
                    maps = await dataMapper(1, json["beatmapsets"])
                    for m in maps:
                        if isinstance(m, ApiResponse):
                            await insertBeatmapsetData(m)
                        else:
                            print("[DATABASE][ERROR] Something went wrong")
                    
                    print(json["cursor_string"])
                    return json["cursor_string"]

                if response.status == 401:
                    print("[API][WARN] HTTP 401, Reauthenticating")
                    await authenticate()
                    print("[API][INFO] Retrying beatmap data fetch")
                    return await getMaps()
                
        except aiohttp.ClientError as e:
            print(f"[AIOHTTP][ERROR] Something went wrong with the client\n{e}")
            return None
                
    cursorString = await getMaps()

    while cursorString is not None:
        cursorString = await getMaps(cursorString)

async def getAllQualifiedIds():
    ids = []
    async def getMaps(cursorString = None):
        try:
            connector = aiohttp.TCPConnector(family = socket.AF_INET)
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {accessToken}"
            }
            async with aiohttp.ClientSession(connector = connector, headers = headers) as session:
                response = await session.get(url = f"{BASEURL}/beatmapsets/search?nsfw=true&s=qualified&cursor_string={cursorString}")
                
                if response.status == 200:
                    print("[API][INFO] Successfully got beatmap json")
                    json = await response.json()
                    
                    for beatmap in json["beatmapsets"]:
                        ids.append(beatmap["id"])
                    
                    print(f"[API][INFO] Cursor string: {json['cursor_string']}")
                    return json["cursor_string"]

                if response.status == 401:
                    print("[API][WARN] HTTP 401, Reauthenticating")
                    await authenticate()
                    
                    print("[API][INFO] Retrying beatmap json fetch")
                    _cursorString = await getMaps(cursorString)
                    return _cursorString
                    
        except aiohttp.ClientError as e:
            print(f"[AIOHTTP][ERROR] Something went wrong with the client\n{e}")
            return None
        
    cursorString = await getMaps()

    while cursorString is not None:
        cursorString = await getMaps(cursorString)
    
    return ids
