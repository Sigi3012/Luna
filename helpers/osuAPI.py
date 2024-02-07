import aiohttp
import socket
from main import Config
from helpers.database import insertBeatmapData

from statistics import StatisticsError, mode

config = Config.getMainInstance()

BASEURL = "https://osu.ppy.sh/api/v2"
GRANTURL = "https://osu.ppy.sh/oauth/token"
CLIENTSECRET = config.osusecret
CLIENTID = config.clientid

accessToken = None

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
                return(json["access_token"])
                
            except Exception as e:
                print(f"[API][ERROR] Something went wrong while accessing the osu!API\n{e}")
        
    except aiohttp.ClientError as e:
        print(f"[AIOHTTP][ERROR] Something went wrong with the client\n{e}")
        return None

async def getBeatmap(id):
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
                    return(data)
                
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
                    
                    for beatmap in json["beatmapsets"]:
                        await insertBeatmapData(
                            beatmap["id"],
                            beatmap["title"],
                            beatmap["artist"],
                            beatmap["creator"],
                            beatmap["submitted_date"],
                            beatmap["ranked_date"],
                            await mostCommonMode(beatmap)
                        )
                    
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

    while cursorString != None:
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

    while cursorString != None:
        cursorString = await getMaps(cursorString)
    
    return ids

async def mostCommonMode(data):
    """
    """
    list = []
    for beatmap in data["beatmaps"]:
        list.append(beatmap["mode"])
    
    try:
        result = mode(list)
        
        if result == "osu":
            return "standard"
        elif result == "fruits":
            return "catch"
        else:
            return result
    except StatisticsError:
        return None