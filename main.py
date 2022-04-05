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

def main():
    client = commands.Bot(
        command_prefix="!",
        intents=discord.Intents.all(),
        application_id=app_id
    )

    @client.event
    async def on_ready():
        print(f"{client.user.name} has connected to discord")

    for folder in os.listdir("modules"):
        if os.path.exists(os.path.join("modules", folder, "cog.py")):
            client.load_extension(f"modules.{folder}.cog")
    
    client.run(token)

if __name__ == '__main__':
    main()