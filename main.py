import discord
from discord import app_commands
import json
import time
import re
import asyncio

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def currentTime():
    return time.strftime("%H:%M:%S", time.localtime())

async def missingPermissions(interaction):
    await interaction.response.send_message("You dont have permissions to do this!", ephemeral=True)

with open("config.json", "r") as file:
    config = json.load(file)
    
if config["firstRun"]:
    print("Thank you for using my bot!\nTo enable the fixer use '/toggle' (admin perms required)")
    config["firstRun"] = not config["firstRun"]
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
    
@tree.command(
    name = "toggle",
    description = "This enables or disables the fixer")
async def togglefixer(interaction):
    if interaction.user.id == int(config["admin"]):
        config['enabled'] = not config['enabled']
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await interaction.response.send_message(f"Toggled to {config['enabled']}", ephemeral=True)
        print(f"Toggled to: {config['enabled']}@{currentTime()}")
    else:
        await missingPermissions(interaction)
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not config["enabled"]:
        return
    async def match(result):
        print("Match found")
        await message.reply(f"<@{message.author.id}>: {result}")
        await asyncio.sleep(1e-3)
        await message.delete()
    VXPATTERN = r'https?://(?:www\.)?(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)(?:/photo/\d)?'
    VXREPLACEMENT = r'https://vxtwitter.com/\1/status/\2'
    DDPATTERN = r'https?://(?:www\.)?instagram\.com\/reel\/([a-zA-Z0-9_-]+)(\/\?igshid=[a-zA-Z0-9_-]+)?'
    DDREPLACEMENT = r'https://ddinstagram.com/reel/\1\2'
    TTPATTERN = r'https:\/\/(?:www\.)?tiktok\.com\/@([^\/]+)\/video\/(\d+)'
    TTREPLACEMENT = r'https://vxtiktok.com/@\1/video/\2'
    vxresult = re.sub(VXPATTERN, VXREPLACEMENT, message.content)
    ddresult = re.sub(DDPATTERN, DDREPLACEMENT, message.content)
    ttresult = re.sub(TTPATTERN, TTREPLACEMENT, message.content)
    if vxresult != message.content:
        await  match(vxresult)
    if ddresult != message.content:
        await match(ddresult)
    if ttresult != message.content:
        await match(ttresult)
    
@tree.command(name= "shutdown", description = "turns off the bot!")
async def shutdown(interaction):
    if interaction.user.id == int(config["admin"]):
        await interaction.response.send_message("Shutting down...", delete_after=3.0, ephemeral=True)
        print(f"Bot offline@{currentTime()}")
        await client.close()
    else:
        await missingPermissions(interaction)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Online!@{currentTime()}")
    print(f"Config loaded!@{currentTime()}")

if __name__ == "__main__":    
    client.run(config["token"])