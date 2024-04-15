import aiosqlite
import time
from main import Config
from helpers.osuAPI import ApiResponse

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
                beatmapsetId INTEGER NOT NULL,
                statusChangeDate TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS aiBlacklist (
                userId INTEGER NOT NULL,
                UNIQUE(userId)
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
   
async def insertBeatmapsetData(mappedData: ApiResponse):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        
        try:
            existingEntry = await cursor.execute("SELECT * FROM beatmapsets WHERE beatmapsetId = ?", (mappedData.beatmapsetId,))
            
            if await existingEntry.fetchone() is not None:
                print(f"[DATABASE][INFO] beatmapsetId {mappedData.beatmapsetId} already exists. Skipping insertion.")
                return
            
            await cursor.execute("INSERT OR IGNORE INTO beatmapsets VALUES (?, ?)",
                (
                    mappedData.beatmapsetId,
                    mappedData.statusChangedDate
                )
            )
            title = mappedData.title
        
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
            await cursor.execute("DELETE FROM beatmapsets WHERE beatmapsetId = ?", (id,))
            await db.commit()
            print(f"[DATABASE][INFO] Successfully deleted {id}")
        
        except Exception as e:
            print(f"[DATABASE][ERROR] Something went wrong while deleting entry!\n{e}")

async def getDatabaseEntry(id: int):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        try:
            selection = await cursor.execute("SELECT * FROM beatmapsets WHERE beatmapsetId = ?", (id,))
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
            selection = await cursor.execute("SELECT beatmapsetId FROM beatmapsets")
            ids = await selection.fetchall()
            print("[DATABASE][INFO] Successfully fetched all beatmapsetIds")
            return [id[0] for id in ids]
        except Exception as e:
            print(f"[DATABASE][ERROR] Something went wrong while fetching ids\n{e}")
            return None

async def addToBlacklist(userId: int):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        try:
            await cursor.execute("INSERT OR IGNORE INTO aiBlacklist VALUES (?)", (userId,))
        except Exception as e:
            print(f"[DATABASE][ERROR] Something went wrong while inserting into blacklist\n{e}")
            return None

        await db.commit()
        print(f"[DATABASE][INFO] Successfully inserted {userId} into aiBlacklist")
        return True

async def removeFromBlacklist(userId: int):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        try:
            await cursor.execute("DELETE FROM aiBlacklist WHERE userId = ?", (userId,))
        except Exception as e:
            print(f"[DATABASE][ERROR] Something went wrong while removing from blacklist\n{e}")
            return None

        await db.commit()
        print(f"[DATABASE][INFO] Successfully removed {userId} from aiBlacklist")
        return True

async def loadBlacklist():
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        try:
            selection = await cursor.execute("SELECT * FROM aiBlacklist")
            ids = await selection.fetchall()
            ids = [id[0] for id in ids]

            return ids
        except Exception as e:
            print(f"[DATABASE][ERROR] Something went wrong while loading ids from blacklist\n{e}")
            return None
