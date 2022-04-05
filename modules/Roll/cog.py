import random
import sys
from discord.ext import commands
import discord

DIE_TYPES = [4, 6, 8, 10, 12, 20]

class Roll(commands.Cog, name="Roll Cog"):

    def __init__(self,  bot: commands.Bot):
        random.seed()
        self.bot = bot

    @commands.command(pass_context=True)
    async def roll(self, ctx: commands.Context, arg):
        """
        !roll xdyy
        """
        num_die = 0
        die_type = 0
        summ = 0           
        output = []

        try:
            uinput = arg.lower()
            split_input = uinput.split("d", 1)

            num_die = int(split_input[0])
            die_type = int(split_input[1])

            if(num_die > 20 or die_type > 20):
                print("Input must be in range 1-20 for number of dice or a valid die type")
            else:
                if die_type not in DIE_TYPES:
                    print("not a valid die_type")
                else:
                    for die in range(num_die):
                        output.append(random.randint(1, die_type))
            
            if(len(output) > 0):
                summ = sum(output)
                await ctx.send(f'{ctx.message.author.display_name} rolled {num_die} D{die_type}\nResults: `{output}`\nDice total: {summ}') # ` ` are used for embedded style text 
            else:
                await ctx.send(f'!roll - Invalid command usage')

        except ValueError as err:
            print("Invalid input", err)
        else:
            print(f'{ctx.message.author.display_name} used Roll')

def setup(bot: commands.Bot):
    bot.add_cog(Roll(bot))