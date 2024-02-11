import aiosqlite
import time
from main import Config

from typing import Optional

config = Config.getMainInstance()

DATABASE = "./persistent/database.db"

async def createTables():
   async with aiosqlite.connect(DATABASE) as db:
       # Create cooldown table
       await db.execute("""
           CREATE TABLE IF NOT EXISTS cooldown (
               userID INTEGER NOT NULL,
               commandTime TIMESTAMP NOT NULL
           )
       """)
       
       # Create beatmapsets table
       await db.execute("""
            CREATE TABLE IF NOT EXISTS beatmapsets (
                beatmapId INTERGER NOT NULL,
                title TEXT,
                artist TEXT,
                creatorName TEXT,
                submittedDate TIMESTAMP,
                qualifiedDate TIMESTAMP,
                mostCommonGamemode TEXT
           )
       """)
       
       await db.commit()

async def checkCooldown(userId):
   async with aiosqlite.connect(DATABASE) as db:
       cursor = await db.cursor()
       await cursor.execute("SELECT commandTime FROM cooldown WHERE userID = ?", (userId,))
       
       row = await cursor.fetchone()
       if row is not None:
           lastCommandTime = row[0]
           cooldownEndTime = lastCommandTime + (config.cooldownMinutes * 60)
           
           if time.time() < cooldownEndTime:
               return cooldownEndTime - time.time()
           else:
               # If the cooldown time has expired, replace it with the new time
               await cursor.execute("UPDATE cooldown SET commandTime = ? WHERE userID = ?", (time.time(), userId))
       else:
           # If the user ID does not exist in the database, insert a new cooldown time
           await cursor.execute("INSERT INTO cooldown VALUES (?, ?)", (userId, time.time()))
       await db.commit()
       return 0
   
async def insertBeatmapData(
    id: int,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    creatorName: Optional[str] = None,
    submittedDate: Optional[str] = None,
    qualifiedDate: Optional[str] = None,
    mostCommonGamemode: Optional[str] = None
    ):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        
        try:
            existingEntry = await cursor.execute("SELECT * FROM beatmapsets WHERE beatmapId = ?", (id,))
            
            if await existingEntry.fetchone() is not None:
                print(f"[DATABASE][INFO] beatmapId {id} already exists. Skipping insertion.")
                return
            
            if title is not None:
                await cursor.execute("INSERT OR IGNORE INTO beatmapsets VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                    id,
                    title,
                    artist,
                    creatorName,
                    submittedDate,
                    qualifiedDate,
                    mostCommonGamemode
                    )
                )
            else:
                from helpers.osuAPI import getBeatmap, mostCommonMode
                data = await getBeatmap(id)
                mostCommonGamemode = await mostCommonMode(data)
                await cursor.execute("INSERT OR IGNORE INTO beatmapsets VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        id,
                        data["title"],
                        data["artist"],
                        data["creator"],
                        data["submitted_date"],
                        data["ranked_date"],
                        mostCommonGamemode
                    )
                )
                title = data["title"]
        
        except Exception as e:
            print(f"[DATABASE][ERROR] Something went wrong while inserting data\n{e}")
            return None

        await db.commit()            
        print(f"[DATABASE][INFO] Successfully inserted data for {title}")
        return

async def deleteBeatmapEntry(id: int):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        try:
            await cursor.execute("DELETE FROM beatmapsets WHERE beatmapId = ?", (id,))
            await db.commit()
            print(f"[DATABASE][INFO] Successfully deleted {id}")
        
        except Exception as e:
            print(f"[DATABASE][ERROR] Something went wrong while deleting entry!\n{e}")

async def getDatabaseEntry(id: int):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        try:
            selection = await cursor.execute("SELECT * FROM beatmapsets WHERE beatmapId = ?", (id,))
            data = await selection.fetchone()
            
            if data is None:
                print(f"[DATABASE][WARN] {id} is not in the database")
                return None

            print("[DATABASE][INFO] Successfully got beatmap information")
            return data

        except Exception as e:
            print(f"[DATABASE][ERROR] Something went wrong while fetching an entry!\n{e}")

async def getAllDatabaseIds():
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        try:
            selection = await cursor.execute("SELECT beatmapid FROM beatmapsets")
            ids = await selection.fetchall()
            print("[DATABASE][INFO] Successfully fetched all beatmapids")
            return [id[0] for id in ids]
        except Exception as e:
            print(f"[DATABASE][ERROR] Something went wrong while fetching ids\n{e}")
            return None