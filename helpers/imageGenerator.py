from helpers.constants import FONT
from io import BytesIO
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageColor
)
import requests
import os

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
    
    if os.path.exists(cachePath):
        resized = Image.open(cachePath)
    else:
        print("Profile picture not in cache, fetching...")
        
        response = requests.api.get(pfpURL)
        pfpImage = Image.open(BytesIO(response.content))
        
        resized = pfpImage.resize((80, 80))
        resized.save(cachePath)

    image.paste(resized, (10, 10), maskPath)
    
    font = ImageFont.truetype(FONT, size=25)
    draw.text((105, 10), username, font=font, fill=(roleColour))
    
    font = ImageFont.truetype(FONT, size=15)
    draw.text((220, 75), time, font=font, fill="white")
    draw.text((105, 50), f'"{message}"', font=font, fill="white")
    
    image.save("./cache/quoteOutput.png")
