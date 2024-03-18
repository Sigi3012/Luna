from __future__ import annotations

import discord
from discord.ext import commands, tasks
from discord import app_commands

from main import Config
from helpers.osuAPI import ApiResponse, authenticate, getBeatmap, populateDatabase, getAllQualifiedIds
from helpers.database import insertBeatmapsetData, deleteBeatmapEntry, getAllDatabaseIds
from helpers.checks import missingPermissions

import asyncio

from typing import List, Literal

import time
from datetime import datetime

config = Config.getMainInstance()
osuChannel = int(config.osuchannel)

MAPFEEDUPDATECOOLDOWN = 30 # Minutes

# --------- #

async def buildEmbed(mappedData: ApiResponse) -> discord.Embed | None:
    """
    This function returns the discord.Embed object
    Params:
        id = osu! beatmap id
        status = osu! beatmap ranking status, defualt is qualified
        https://osu.ppy.sh/docs/index.html#beatmapset-rank-status
        
    Checks database if the id is in it, if not then osuAPI.py getBeatmap is ran
    """
    
    # --------- #
    
    async def replaceSpaces(string):
        result = ""
        for character in string:
            if character == " ":
                result += '%20'
            else:
                result += character
        return result

    # --------- #

    beatmapStatuses = {
        -1: "Disqualified",
        0: "Disqualified",
        1: "Ranked",
        3: "Qualified",
        4: "Loved"
    }
    
    try:
        beatmapStatus = beatmapStatuses[mappedData.status]
    except Exception as e:
        print(f"Genuinely how did this happen.. Error: {e}")
        return None
    
    # --------- #
    
    submittedUnix = int(time.mktime(mappedData.submittedDate.timetuple()))
    
    # This means the status has gone back to pending
    if mappedData.statusChangedDate is None:
        statusChangeUnix = ""
    else:
        statusChangeUnix = f"<t:{int(time.mktime(mappedData.statusChangedDate.timetuple()))}:R>" 
    
    # --------- #
        
    starRating = [beatmap.starRating for beatmap in mappedData.beatmaps]
    
    lowestStarRating: float = min(starRating)
    highestStarRating: float = max(starRating)
    
    displayStarRating = f"{lowestStarRating} - {highestStarRating} \U00002605"
    
    if lowestStarRating == highestStarRating:
        displayStarRating = highestStarRating
    
    # --------- #
    
    if beatmapStatus == "Qualified":
        # 🟧
        embedColour = 0xD1a03D
    
    if beatmapStatus == "Ranked":
        # 🟦
        embedColour = 0x405ac9
    
    if beatmapStatus == "Loved":
        # 🟪 There was no pink squre
        embedColour = 0xFF69B4

    if beatmapStatus == "Disqualified":
        # 🟥 
        embedColour = 0xD22B2B
        
    # --------- #
    
    # Looks like this https://imgur.com/a/AIQpgOG
    embed = discord.Embed(
        description = f"**[{mappedData.title}](https://osu.ppy.sh/beatmapsets/{mappedData.beatmapsetId})** | **{beatmapStatus} {statusChangeUnix}**\n"
                      f"Mapped by [{mappedData.mapper}](https://osu.ppy.sh/users/{await replaceSpaces(mappedData.mapper)}) | [osu!{mappedData.mostCommonMode}]\n"
                      f"Artist: {mappedData.artist}\n"
                      f"Submitted: <t:{submittedUnix}:R>\n"
                      f"\n{displayStarRating} \U00002022 {len(mappedData.beatmaps)} Difficulties",
        colour = embedColour,
    )
    embed.set_image(url = f"https://assets.ppy.sh/beatmaps/{mappedData.beatmapsetId}/covers/card.jpg")
    embed.set_footer(text = f"Made by @.Sigi")
    
    print(f"Title: {mappedData.title}\nArtist: {mappedData.artist}\nCreator name: {mappedData.mapper}\nSubmitted date: {mappedData.submittedDate}\nQualified Date: {mappedData.statusChangedDate}\nBeatmap status: {beatmapStatus}")

    return embed

# --------- #

class Maps(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")

    async def cog_unload(self):
        self.mapfeedTask.cancel()
        
    @tasks.loop(minutes = MAPFEEDUPDATECOOLDOWN)
    async def mapfeedTask(self):
        await self.updateMapFeed()
    
    @mapfeedTask.before_loop
    async def beforeMapfeed(self):
        await self.client.wait_until_ready()
    
    async def updateMapFeed(self):
        """
        Flow chart: https://imgur.com/a/fAlHfE4
        This implementation does not follow the flow chart exactly.
        """
        #calls once
        qualifiedIds = await getAllQualifiedIds()
        
        databaseIds = await getAllDatabaseIds()
        
        if qualifiedIds is None or databaseIds is None:
            print("[MAPS][ERROR] Aborting!")
            return None
        
        # If in GET not in db
        newMaps = [a for a in qualifiedIds if a not in databaseIds]
        # If in db not in GET
        changedStatusMaps = [b for b in databaseIds if b not in qualifiedIds]
        # If in db and in GET
        commonMaps = [c for c in databaseIds if c in qualifiedIds]
        
        print(f"New maps: {newMaps}")
        print(f"Changed map: {changedStatusMaps}")
        print(f"Common maps {commonMaps}")
        
        channel = self.client.get_channel(osuChannel)
        
        async def processNewMaps(ids: List[int]):
            for id in ids:
                data: ApiResponse = await getBeatmap(id)
                
                embed = await buildEmbed(data)        
                await channel.send(embed = embed)
                
                await insertBeatmapsetData(data)
        
        async def processChangedMaps(ids: List[int]):
            for id in ids:
                data: ApiResponse = await getBeatmap(id)

                embed = await buildEmbed(data)
                await channel.send(embed = embed)
                
                await deleteBeatmapEntry(data.beatmapsetId)

        await asyncio.gather(
            processNewMaps(newMaps),
            processChangedMaps(changedStatusMaps)
        )
              
        print("[TASK][INFO] Completed")
    
    
    @app_commands.command(name = "auth", description = "Returns an access token")
    async def auth(self, interaction: discord.Interaction):
        if interaction.user.id == int(config.admin):
            accessToken = await authenticate()
            await interaction.response.send_message(content = f"```{accessToken}```", ephemeral = True)
        else:
            await missingPermissions(interaction)
    
    @app_commands.command(name = "populatedb", description = "Inserts current qualified maps")
    async def getqualified(self, interaction: discord.Interaction):
        if interaction.user.id == int(config.admin):
            try:
                await populateDatabase()
                await interaction.response.send_message("Successfully populated database with current qualified maps")
            except Exception:
                await interaction.response.send_message(f"Something went wrong!")
        else:
            await missingPermissions(interaction)

    @app_commands.command(name = "delete", description = "Delete an entry")
    async def delete(self, interaction: discord.Interaction, id: int):
        if interaction.user.id == int(config.admin):
            await deleteBeatmapEntry(id)
            await interaction.response.send_message(f"Deleted {id} successfully!")
        else:
            await missingPermissions(interaction)
            
    @app_commands.command(name = "mapfeed", description = "Controls for the osu!mapfeed")
    async def mapfeed(self, interaction: discord.Interaction, option: Literal["Start", "Stop", "Restart", "Force", "Status"]):
        if interaction.user.id == int(config.admin):
            state = self.mapfeedTask.is_running()
            
            async def reply():
                await interaction.response.send_message("Successful", ephemeral = True)
            
            if option == "Start":
                if state == True:
                    await interaction.response.send_message(f"The task is already started!", ephemeral = True)
                else:
                    self.mapfeedTask.start()
                    print("[TASK][INFO] Mapfeed started")
                    await reply()

            if option == "Stop":
                if state == False:
                    await interaction.response.send_message(f"The task is already stopped!", ephemeral = True)
                else:
                    self.mapfeedTask.cancel()
                    print("[TASK][INFO] Mapfeed stopped")
                    await reply()
                    
            if option == "Restart":
                self.mapfeedTask.restart()
                print("[TASK][INFO] Mapfeed restarted")
                await reply()

            if option == "Force":
                await self.updateMapFeed()
                print("[TASK][INFO] Mapfeed force refreshed")
                await reply()
            
            if option == "Status":
                await interaction.response.send_message(state, ephemeral = True)
        else:
            missingPermissions(interaction)
    
    @commands.is_owner()      
    @commands.command()
    async def getmap(self, ctx: commands.Context, id):
        data = await getBeatmap(id)
        await ctx.reply(data)
            
# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Maps(client))
