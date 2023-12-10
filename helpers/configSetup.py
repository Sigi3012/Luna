import json
import os
from dotenv import load_dotenv

load_dotenv()

# This is held together with sheer will power and sticky tape 
# I dont fully understand how it works but it does

# --------- #

class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            return cls._instance
        else:
            raise Exception("An instance of Config already exists. Use Config.get_instance() to access it.")

    def __init__(self, path="config.json"):
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
        self.admin = os.getenv("ADMIN")
        self.qoutechannelid = os.getenv("QUOTECHANNELID")

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
