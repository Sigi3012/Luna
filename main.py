import discord
from discord import app_commands
import json
import re

intents = discord.Intents.all()
client = discord.client(intents=intents)
tree = app_commands.CommandTree(client)

with open("config.json", "r") as file:
    config = json.load(file)
    print("loaded config")
    
if __name__ == "__main__":    
    client.run(config["token"])