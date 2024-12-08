import discord
import os
import sys
import shutil
import logging
import asyncio
import aiohttp
import requests
import aiosqlite
import aiocache
import aiofiles
import traceback
import pkgutil
from discord.ext import commands, tasks
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv()

class Bot(commands.AutoShardedBot):
    def __init__(self) -> None:
        super().__init__(
            intents=discord.Intents.all(),
            command_prefix=';',
            owner_ids={
                1234903841611317251,
                1263092918130966569
            },
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name='/help | rix.com'
            ),
            status=discord.Status.online,
            max_messages=1000,
            help_command=None,
            case_insensitive=True
        )
        self.logger = None
        self.cache = None
        

    async def setup_hook(self) -> None:
        await self.setup_logging()
        await self.setup_database()
        await self.setup_cache()  
        await self.load_cogs()
        
    async def setup_logging(self) -> None:
        os.makedirs('src/logging', exist_ok=True)   

        try:
            logger = logging.getLogger('bot')
            logger.setLevel(logging.DEBUG)

            handler = RotatingFileHandler(
                os.path.join('src/logging', 'bot.log'),
                encoding='UTF-8', 
                maxBytes=10240, 
                backupCount=3
                )
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                )
            logger.addHandler(handler)
            print('Logging have been setup successfully')
        except Exception:
            print('An error occurred while setup the logging:')
            traceback.print_exc()
        
    async def setup_database(self) -> None:
        os.makedirs('src/database', exist_ok=True)  

        try:
            async with aiosqlite.connect(os.path.join('src/database', 'bot.db')) as database:
                async with database.cursor() as cursor:
                    async with aiofiles.open('src/database/schemas.sql', mode='r') as schema:
                        await cursor.executescript(await schema.read())
                        await database.commit()      
            print('Database have been setup successfully')
        except Exception:
            print('An error occurred while setup the database:')
            traceback.print_exc()
            
    async def setup_cache(self) -> None:
        try:
            self.cache = aiocache.SimpleMemoryCache()
            print('Cache have been setup successfully')
        except Exception:
            print('An error occurred while setup the cache:')
            traceback.print_exc()
        
    async def load_cogs(self) -> None:
        os.makedirs('src/cogs', exist_ok=True) 
        for _, cog, _ in pkgutil.iter_modules(['src/cogs']):
            if cog != '__pycache__':
                try:
                    if cog not in self.extensions:
                        await self.load_extension(f'src.cogs.{cog}')
                        print(f'Loaded cog: {cog}')
                except Exception:
                    print(f'Failed to load cog: {cog}')
                    traceback.print_exc()

    async def mobile_gateway(self) -> None:
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'token': self.token,
                'properties': {
                    '$os': sys.platform,
                    '$browser': 'Discord iOS',
                    '$device': 'discord.py',
                },
                'large_threshold': 250,
                'compress': True,
                'v': 10,
            },
        }
        
        if self.shard_id is not None and self.shard_count is not None:
            payload['d']['shard'] = [self.shard_id, self.shard_count]

        if self._connection._status or self._connection._activity:
            payload['d']['presence'] = {
                'status': self._connection._status,
                'activities': [self._connection._activity],
                'since': 0,
            }

        if self._connection._intents:
            payload['d']['intents'] = self._connection._intents.value

        await self.call_hooks('before_identify', self.shard_id, initial=self._initial_identify)

        await self.send_as_json(payload)

def main() -> None:
    discord.gateway.DiscordWebSocket.identify = Bot.mobile_gateway
    Bot().run(os.getenv('BOT_TOKEN'), reconnect=True)

if __name__ == '__main__':
    main()
