import discord
from discord import app_commands
import json
import re

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

with open("config.json", "r") as file:
    config = json.load(file)
    print("loaded config")
    
@tree.command(
    name = "toggle",
    description = "This enables or disables the fixer")
@app_commands.checks.has_permissions(administrator=True)
async def togglefixer(interaction):
    config['enabled'] = not config['enabled']
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    await interaction.response.send_message(f"Toggled to {config['enabled']}", ephemeral=True)
@tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You dont have permissions to do this!", ephemeral=True)
    
@client.event
async def on_ready():
    await tree.sync()
    print("Online!")

if __name__ == "__main__":    
    client.run(config["token"])