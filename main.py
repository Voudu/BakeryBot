from dotenv import load_dotenv
from discord.ext import commands

import sys
import os
import discord

load_dotenv()
token = os.getenv("TOKEN")
app_id = os.getenv("APP_ID")
guild_id = os.getenv("GUILD_ID")

sys.path.append(".")

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            application_id=app_id
        )

    async def setup_hook(self):
        for folder in os.listdir("modules"):
            if os.path.exists(os.path.join("modules", folder, "cog.py")):
                await self.load_extension(f"modules.{folder}.cog")

        await self.tree.sync(guild = discord.Object(id=guild_id))

    # async def close(self):
    #     await super().close()
    #     await self.session.close()

    async def on_ready(self):
        print(f"{self.user.name} has connected to discord")

bot = MyBot()
bot.run(token)