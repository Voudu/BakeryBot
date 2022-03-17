import sys
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option

load_dotenv()
token = os.getenv("TOKEN")

sys.path.append(".")

def main():
    client = commands.Bot(command_prefix="!")

    @client.event
    async def on_ready():
        print(f"{client.user.name} has connected to Discord")

    for folder in os.listdir("modules"):
        if os.path.exists(os.path.join("modules", folder, "cog.py")):
            client.load_extension(f"modules.{folder}.cog")

    # should learn how to move this to an environment variable
    client.run(token)

if __name__ == '__main__':
    main()