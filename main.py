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
@app_commands.checks.has_permissions(administrator=True)
async def togglefixer(interaction):
    config['enabled'] = not config['enabled']
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    await interaction.response.send_message(f"Toggled to {config['enabled']}", ephemeral=True)
    print(f"Toggled to: {config['enabled']}@{currentTime()}")
@tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You dont have permissions to do this!", ephemeral=True)
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not config["enabled"]:
        return
    
    async def match(result):
        print("Match found")
        await message.reply(f"<@{message.author.id}>: {result}", silent=True)
        await asyncio.sleep(1e-3)
        await message.delete()
        
    VXPATTERN = r'https?://(?:www\.)?(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)(?:/photo/\d)?'
    VXREPLACEMENT = r'https://vxtwitter.com/\1/status/\2'
    DDPATTERN = r'https?://(?:www\.)?instagram\.com\/reel\/([a-zA-Z0-9_-]+)(\/\?igshid=[a-zA-Z0-9_-]+)?'
    DDREPLACEMENT = r'https://ddinstagram.com/reel/\1\2'
    TTPATTERN = r'https:\/\/(?:www\.|vm\.)?tiktok\.com\/@([^\/]+)\/video\/(\d+)'
    TTREPLACEMENT = r'https://vxtiktok.com/@\1/video/\2'
    VMPATTERN = r'https:\/\/vm\.tiktok\.com\/([\[A-Za-z0-9]+)'
    VMREPLACEMENT = r'https://vm.vxtiktok.com/\1'
    PXPATTERN = r'https:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?(?:artworks|member_illust)\/(\d+)'
    PXREPLACEMENT = r'https://phixiv.net/artworks/\1'
    
    endResult = re.sub(VXPATTERN, VXREPLACEMENT, message.content)
    endResult = re.sub(DDPATTERN, DDREPLACEMENT, endResult)
    endResult = re.sub(TTPATTERN, TTREPLACEMENT, endResult)
    endResult = re.sub(VMPATTERN, VMREPLACEMENT, endResult)
    endResult = re.sub(PXPATTERN, PXREPLACEMENT, endResult)
    if endResult != message.content:
        await match(endResult)
    
@tree.command(name= "shutdown", description = "turns off the bot!")
@app_commands.checks.has_permissions(administrator=True)
async def shutdown(interaction):
    await interaction.response.send_message("Shutting down...", delete_after=3.0, ephemeral=True)
    print(f"Bot offline@{currentTime()}")
    await client.close()
@tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You dont have permissions to do this!", ephemeral=True)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Online!@{currentTime()}")
    print(f"Config loaded!@{currentTime()}")

if __name__ == "__main__":    
    client.run(config["token"])