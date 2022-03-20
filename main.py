from dotenv import load_dotenv
from discord.ext import commands

import sys
import os
import discord

# TODO:
#   - make this into a class

load_dotenv()
token = os.getenv("TOKEN")

sys.path.append(".")

def main():
    client = commands.Bot(
        command_prefix="!",
        intents=discord.Intents.all(),
        application_id=os.getenv("APP_ID"),
        test_guilds=[633847600403054592]
    )

    @client.event
    async def on_ready():
        print(f"{client.user.name} has connected to discord")

    async def setup_hook(self):
        for folder in os.listdir("modules"):
            if os.path.exists(os.path.join("modules", folder, "cog.py")):
                await client.load_extension(f"modules.{folder}.cog")

    # TODO
    # await bot.tree.sync(guild = discord.Object(id= guild_id))

    # TODO
    # implement the following
    # async def close(self):
    #   await super().close()
    #   await self.sessions.close()

    # should learn how to move this to an environment variable
    client.run(token)

if __name__ == '__main__':
    main()