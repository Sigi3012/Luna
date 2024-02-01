from discord.ext import commands
from main import Config
import discord
from datetime import datetime

config = Config.getMainInstance()

# --------- #

class Misc(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        
        self.options = [
            "guild_update", "channel_create", "channel_update", "channel_delete", "overwrite_create",
            "overwrite_update", "overwrite_delete", "kick", "ban", "unban", "member_update",
            "member_role_update", "member_move", "member_disconnect", "role_create", "role_update",
            "role_delete", "invite_create", "invite_delete", "emoji_create", "emoji_update", "emoji_delete",
            "sticker_create", "sticker_update", "sticker_delete", "message_delete", "message_pin",
            "message_unpin", "automod_block_message", "automod_flag_message"
        ]
        
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")
        self.moderationChannel = self.client.get_channel(int(config.modchannel))
        
    # --------- #
        
    async def buildEmbed(self, action, user, before, after, target):
        print("New entry")
        _before = dict(before)
        _after = dict(after)
        
        try:
            targetName = target.name
            targetDescription = target.description
            
            targetString = f"Target: {targetName}\n{targetDescription}\n\n"
        except AttributeError:
            targetString = None

        for key, value in _before.items():
            beforekey = key
            beforevalue = value
            
        for key, value in _after.items():
            afterkey = key
            aftervalue = value
            
        e = discord.Embed(
            title = action,
            description = f"{targetString}Before: {beforekey} = {beforevalue}\nAfter: {afterkey} = {aftervalue}",
            colour = 0x383cc6,
            timestamp = datetime.now()
        )
        e.set_author(name = user.global_name, icon_url = user.avatar.url)
        await self.moderationChannel.send(embed = e)
        
    # --------- #

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if config.modchannel == None:
            return
        
        print("cute and fnny")
        print(entry.action.name)
        print(entry.user.global_name)
        print(entry.before)
        print(entry.after)
        print(entry.target)
        
        await self.buildEmbed(
            entry.action.name,
            entry.user,
            entry.before,
            entry.after,
            entry.target
        )
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        
        if message.content == "!gay":
            await message.reply("https://tenor.com/view/bronya-seele-bronyaseele-seele-x-bronya-bronya-x-seele-gif-22095999")

# --------- #


async def setup(client:commands.Bot) -> None:
    await client.add_cog(Misc(client))
