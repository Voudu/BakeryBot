import discord
from discord.ext import commands

class ChatManager(commands.Cog, name="ChatManager Cog"):

    def __init__(self,  bot: commands.Bot):
        self.bot = bot
        self.bot_ignore = False     # this checks if another command is being run or not

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def say(self, ctx: commands.Context, *msg):
        """
        !say message:string

        the bot will output a message in the channel this was called
        """

        msg = " ".join(msg)
        await ctx.channel.send(msg)


    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)       # make sure the person executing has permissions
    async def purge(self, ctx: commands.Context, n:int):
        """
        !purge n:int

        take an int, will delete the last n messages

        clears all messages in the chat channel that this was called from. Requires admin privelages
        """
        try:
            n = int(n)
            channel = ctx.message.channel
        except ValueError as ve:
            print(ve)
            await ctx.channel.send("'!purge n' takes one numeric input (e.g. !purge 20)")
            return

        if self.bot_ignore is True:
            await ctx.channel.send("Please wait for the previous purge command to complete.")
        elif n > 100:
            await ctx.channel.send("Tried to purge more than 100 messages, not allowed.")
        else:
            self.bot_ignore = True
            deleted = await channel.purge(limit=n) 
            print(f"Purged {len(deleted)} message(s)")
        
        self.bot_ignore = False

def setup(bot: commands.Bot):
    bot.add_cog(ChatManager(bot))