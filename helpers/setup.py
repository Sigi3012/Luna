from main import Config

config = Config.getMainInstance()

def setupBot():

    def finish():
        config.update(firstRun=False)
        config.save()
        print("\nThanks for using my bot!")
        print("Now rerun main.py")
        exit()

    while True:
        try:
            completed = input("Have you already setup your config.json? y/n: ")
            if completed.lower() == "y":
                finish()
                return
            elif completed.lower() == "n":
                break
            else:
                raise ValueError("Invalid Input")
        except ValueError as e:
            print(e)

    print("First add in your token\nGo to Discord dev portal and click on your application > Bot > Reset Token, then paste it in here\nhttps://discord.com/developers/applications\n")
    while True:
        try:
            newToken = input("> ")
            if newToken != "":
                config.update(token=newToken)
                break
            else:
                raise ValueError("Enter a bot token")
        except ValueError as e:
            print(e)
    print("Now input your userID below, you need to turn on developer settings in discord, then rightclick your profile\nmake sure its yours or none of the admin commands will work")
    while True:
        try:
            newUID = input("> ").strip()
            if newUID != "":
                test = int(newUID)
                config.update(admin=str(newUID))
                break
            else:
                raise ValueError("Cannot be string or None")
        except ValueError as e:
            print(e)
    print("Do you want to allow the bot to fix links in NSFW channels?")
    while True:
        try:
            nsfw = input("y/n\n> ")
            if nsfw.lower() == "y":
                config.update(nsfwAllowed=True)
                break
            elif nsfw.lower() == "n":
                break
            else:
                raise ValueError("Invalid choice")
        except ValueError as e:
            print(e)
    
    finish()
    