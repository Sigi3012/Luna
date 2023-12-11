from helpers.constants import FONT
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageColor
)
import aiohttp
import asyncio
import os
import socket

# --------- #

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"}

async def download_image(url):
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        async with session.get(url) as response:
            return await response.read()
        
# --------- #

def process_image(data):
    with Image.open(BytesIO(data)) as img:
        img = img.resize((80, 80))
        outputBuffer = BytesIO()
        img.save(outputBuffer, format="PNG")
        return outputBuffer.getvalue()

# --------- #

async def createQuoteImage(message, pfpURL, username, userid, rolecolour, messagetime):
    if len(message) > 30:
        print("Message is too long")
    
    # Create an image with a grey background
    image = Image.new("RGB", (400, 100), (49, 51, 56))
    draw = ImageDraw.Draw(image)
    roleColour = ImageColor.getrgb(f"{rolecolour}")
    time = messagetime.strftime("%Y/%m/%d %H:%M:%S")
    
    maskPath = Image.open("mask.png")
    cachePath = f"./cache/{userid}.png"
    
    if os.path.exists(cachePath) != True:
        print("Profile picture not in cache, fetching...")        
        image_data = await download_image(pfpURL)
        
        with ThreadPoolExecutor() as pool:
            processed_data = await asyncio.get_event_loop().run_in_executor(pool, process_image, image_data)

        with open(cachePath, "wb") as file:
            file.write(processed_data)
                    
    resized = Image.open(cachePath)

    image.paste(resized, (10, 10), maskPath)
    
    font = ImageFont.truetype(FONT, size=25)
    draw.text((105, 10), username, font=font, fill=(roleColour))
    
    font = ImageFont.truetype(FONT, size=15)
    draw.text((220, 75), time, font=font, fill="white")
    draw.text((105, 50), f'"{message}"', font=font, fill="white")
    
    image.save("./cache/quoteOutput.png")
