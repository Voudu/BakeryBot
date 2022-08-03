from dotenv import load_dotenv
from discord.ext.commands import Bot
from discord import Intents

import asyncio
import sys
import os
import discord

load_dotenv()
token = os.getenv("TOKEN")
app_id = os.getenv("APP_ID")
guild_id = os.getenv("GUILD_ID")
intents = Intents.all()

sys.path.append(".")

client = Bot(
    command_prefix="!",
    intents=intents,
    application_id=app_id
)

async def main():

    @client.event
    async def on_ready():
        print(f"{client.user.name} has connected to discord")

    async with client:
        await load_extensions()
        await client.start(token)

async def load_extensions():
    for folder in os.listdir("modules"):
        if os.path.exists(os.path.join("modules", folder, "cog.py")):
            await client.load_extension(f"modules.{folder}.cog")    

if __name__ == '__main__':
    client.run(token)