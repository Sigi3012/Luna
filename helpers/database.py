import aiosqlite
import time
from main import Config

config = Config.getMainInstance()

async def createTables():
   async with aiosqlite.connect("./cooldowns.db") as db:
       await db.execute("""
           CREATE TABLE IF NOT EXISTS cooldown (
               userID INTEGER NOT NULL,
               commandTime TIMESTAMP NOT NULL
           )
       """)
       await db.commit()

async def checkCooldown(user_id):
   async with aiosqlite.connect("./cooldowns.db") as db:
       cursor = await db.cursor()
       await cursor.execute("SELECT commandTime FROM cooldown WHERE userID = ?", (user_id,))
       
       row = await cursor.fetchone()
       if row is not None:
           lastCommandTime = row[0]
           cooldownEndTime = lastCommandTime + (config.cooldownMinutes * 60)
           
           if time.time() < cooldownEndTime:
               return cooldownEndTime - time.time()
           else:
               # If the cooldown time has expired, replace it with the new time
               await cursor.execute("UPDATE cooldown SET commandTime = ? WHERE userID = ?", (time.time(), user_id))
       else:
           # If the user ID does not exist in the database, insert a new cooldown time
           await cursor.execute("INSERT INTO cooldown VALUES (?, ?)", (user_id, time.time()))
       await db.commit()
       return 0
