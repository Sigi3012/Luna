import aiohttp
import socket
from bs4 import BeautifulSoup

# --------- #

async def scrapeHTML(pinID):
    link = f"https://www.pinterest.co.uk/pin/{pinID}"
    try:
        connector = aiohttp.TCPConnector(family=socket.AF_INET)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(link) as r:
                if r.status == 200:
                    return await r.text()
                else:
                    print("Could not scrape Pinterest page!")
                    return None
    except aiohttp.ClientError as e:
        print(f"Could not scrape Pinterest page!\n{e}")
        return None
    
# --------- #
    
async def getData(html):
    soup = BeautifulSoup(html, "html.parser")
    
    # 0: Image, 1: Title, 2: Profile name
    returnData = []
    
    imageURL = soup.find('meta', {'property': 'og:image'})['content']
    returnData.insert(0, imageURL)
    
    # --------- #
    
    titleClass = soup.find("h1", {"class": "lH1 dyH iFc H2s GTB O2T zDA IZT"})
    if titleClass is not None:
        returnData.insert(1, titleClass.text)
    else:
        returnData.insert(1, None)

    # --------- #

    profileClassesList = [
        "tBJ dyH iFc sAJ O2T zDA IZT H2s CKL",
        "tBJ dyH iFc sAJ O2T zDA IZT H2s",
        "tBJ dyH iFc j1A O2T zDA IZT H2s" 
    ]
    
    index = 0

    while True:
        profileName = soup.find("div", {"class": profileClassesList[index]})
        
        if profileName is not None:
            returnData.insert(2, profileName.text)
            index = 0
            break
        elif index == len(profileClassesList) - 1:
            returnData.insert(2, None)
            index = 0
            break
        else:
            index += 1
    
    # --------- #
    
    return(returnData)