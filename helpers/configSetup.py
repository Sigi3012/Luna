import json
import os
from dotenv import load_dotenv

load_dotenv()

# TODO standardise this and make it less horrible

# --------- #

class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            return cls._instance
        else:
            raise Exception("An instance of Config already exists. Use Config.get_instance() to access it.")

    def __init__(self, path="./persistent/config.json"):
        if not hasattr(self, "initialized"):
            self.path = path
            self.load()
            self.initialized = True

    @classmethod
    def getMainInstance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def load(self):
        with open(self.path, "r") as file:
            data = json.load(file)

        self.token = os.getenv("TOKEN")
        self.osusecret = os.getenv("OSUSECRET")
        self.clientid = os.getenv("CLIENTID")
        self.admin = os.getenv("ADMIN")
        self.qoutechannelid = os.getenv("QUOTECHANNELID")
        self.modchannel = os.getenv("MODCHANNEL")
        self.osuchannel = os.getenv("OSUCHANNEL")
        self.catapikey = os.getenv("CATAPIKEY")

        self.enabled = data["enabled"]
        self.totalFixed = data["totalFixed"]
        self.timeoutTime = data["timeoutTime"]
        self.cooldownMinutes = data["cooldownMinutes"]
        self.nsfwAllowed = data["nsfwAllowed"]

    def save(self):

        data = {
            "enabled": self.enabled,
            "totalFixed": self.totalFixed,
            "timeoutTime": self.timeoutTime,
            "cooldownMinutes": self.cooldownMinutes,
            "nsfwAllowed": self.nsfwAllowed
        }

        with open(self.path, "w") as file:
            json.dump(data, file, indent=4)

    def update(self, enabled=None, totalFixed=None):
        if enabled is not None:
            self.enabled = enabled
        if totalFixed is not None:
            self.totalFixed = totalFixed

    def toggle(self):
        self.enabled = not self.enabled

