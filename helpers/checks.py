from main import Config

config = Config.getMainInstance()

def check():
    if config.admin is not None:
        try:
            test = int(config.admin)
        except ValueError:
            print("Please set a user ID in .env and run the bot again.")
            return False
    else:
        return False

    if len(config.token) < 20:
        print("Please set your discord bot token in the .env, to get your bot token go to the discord developer portal and select your app, then it is found in Bot > Token.")
        return False
   
async def missingPermissions(interaction):
    await interaction.response.send_message("You dont have permissions to do this!", ephemeral=True)