from dotenv import load_dotenv
from disnake.ext.commands import Bot

import sys
import os
import disnake

load_dotenv()
token = os.getenv("TOKEN")

sys.path.append(".")

def main():
    client = Bot(command_prefix="!")

    @client.event
    async def on_ready():
        print(f"{client.user.name} has connected to disnake")

    for folder in os.listdir("modules"):
        if os.path.exists(os.path.join("modules", folder, "cog.py")):
            client.load_extension(f"modules.{folder}.cog")

    # should learn how to move this to an environment variable
    client.run(token)

if __name__ == '__main__':
    main()