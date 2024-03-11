import discord
from discord.ext import commands, tasks
from discord import app_commands

from main import Config
from helpers.osuAPI import authenticate, getBeatmap, populateDatabase, getAllQualifiedIds, mostCommonMode
from helpers.database import insertBeatmapData, deleteBeatmapEntry, getDatabaseEntry, getAllDatabaseIds
from helpers.checks import missingPermissions

import asyncio

from typing import List, Literal

from datetime import datetime
from calendar import timegm

config = Config.getMainInstance()
osuChannel = int(config.osuchannel)

MAPFEEDUPDATECOOLDOWN = 30 # Minutes

# --------- #

async def buildEmbed(id: int, status: int = 3):
    """
    This function returns the discord.Embed object
    Params:
        id = osu! beatmap id
        status = osu! beatmap ranking status, defualt is qualified
        https://osu.ppy.sh/docs/index.html#beatmapset-rank-status
        
    Checks database if the id is in it, if not then osuAPI.py getBeatmap is ran
    """
    response = await getDatabaseEntry(id)

    if response == None or status == None:
        responseData = await getBeatmap(id)

        data = []

        data.append(responseData["id"])
        data.append(responseData["title"])
        data.append(responseData["artist"])
        data.append(responseData["creator"])
        data.append(responseData["submitted_date"])
        data.append(responseData["ranked_date"])
        data.append(await mostCommonMode(responseData))
    
        status = responseData["ranked"]
    else:
        data = list(response)
    
    title = data[1]
    artist = data[2]
    creatorName = data[3]
    submittedDate = data[4]
    statusChangeDate = data[5]
    mostCommonGamemode = data[6]
    
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
        beatmapStatus = beatmapStatuses[status]
    except Exception as e:
        print(f"Genuinely how did this happen.. Error: {e}")
        return None
    
    # --------- #
    
    submittedDatetime = datetime.strptime(submittedDate, "%Y-%m-%dT%H:%M:%SZ")
    submittedUnix = timegm(submittedDatetime.utctimetuple())
    
    # This means the status has gone back to pending
    if statusChangeDate is None:
        statusChangeUnix = ""
    else:
        statusChangeDatetime = datetime.strptime(statusChangeDate, "%Y-%m-%dT%H:%M:%SZ")
        statusChangeUnix = f"<t:{timegm(statusChangeDatetime.utctimetuple())}:R>" 
    
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
        description = f"**[{title}](https://osu.ppy.sh/beatmapsets/{id})** | **{beatmapStatus} {statusChangeUnix}**\n"
                      f"Mapped by [{creatorName}](https://osu.ppy.sh/users/{await replaceSpaces(creatorName)}) | [osu!{mostCommonGamemode}]\n"
                      f"Artist: {artist}\n"
                      f"Submitted: <t:{submittedUnix}:R>",
        colour = embedColour,
    )
    embed.set_image(url = f"https://assets.ppy.sh/beatmaps/{id}/covers/card.jpg")
    embed.set_footer(text = f"Made by @.Sigi")
    
    print(f"Title: {title}\nArtist: {artist}\nCreator name: {creatorName}\nSubmitted date: {submittedDate}\nQualified Date: {statusChangeDate}\nBeatmap stauts: {beatmapStatus}")

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
                embed = await buildEmbed(id)
                await insertBeatmapData(id)
                await channel.send(embed = embed)
        
        async def processChangedMaps(ids: List[int]):
            for id in ids:
                embed = await buildEmbed(id, status = None)
                await deleteBeatmapEntry(id)
                await channel.send(embed = embed)

        await asyncio.gather(
            processNewMaps(newMaps),
            processChangedMaps(changedStatusMaps)
        )
              
        print("[TASK][INFO] Completed")
    
    
    @app_commands.command(name = "auth", description = "Returns an access token")
    async def auth(self, interaction: discord.Interaction):
        if interaction.user.id == int(config.admin):
            accessToken = await authenticate()
            await interaction.response.send_message(accessToken, ephemeral = True)
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
    async def mapfeed(self, interaction: discord.Interaction, option: Literal["Start", "Stop", "Status"]):
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
                    self.mapfeedTask.stop()
                    print("[TASK][INFO] Mapfeed stopped")
                    await reply()
                    
            if option == "Status":
                await interaction.response.send_message(state, ephemeral = True)
        else:
            missingPermissions(interaction)
    
# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Maps(client))
