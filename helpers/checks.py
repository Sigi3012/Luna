import json
def check():
    with open("config.json", "r") as file:
        config = json.load(file)

    if config["admin"] is not None:
        try:
            test = int(config["admin"])
        except ValueError:
            print("Please set a user ID in config.json and run the bot again.")
            exit()

    if config["token"] == "yourtokenhere":
        print("Please set your discord bot token in the config.json, to get your bot token go to the discord developer portal and select your app, then it is found in Bot > Token.")
        exit()
   
    if config["firstRun"]:
        print("Thank you for using my bot!\nTo enable the fixer use '/toggle' (admin perms required)")
        config["firstRun"] = not config["firstRun"]
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

async def missingPermissions(interaction):
    await interaction.response.send_message("You dont have permissions to do this!", ephemeral=True)