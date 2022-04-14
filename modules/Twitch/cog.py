import sys
import os
from dotenv import load_dotenv
from twitchAPI.twitch import Twitch
import twitchAPI
from pprint import pprint
from discord.ext import commands
import discord
import json
import re

# Main Idea:
# Maintain a list of twitch usernames or keys that doesnt change with username changes
# from this list periodically check if the user has gone live.

# SEE: https://dev.twitch.tv/docs/api/reference#get-streams

# If the user is live and they are not currently in the "Live List" then add them to the live list
# ALSO send a notification to the server.

# The live list will store tuples, [(user, start_time), (user, start_time)]

# If a user goes OFFLINE during the next check, we check the streams and first compare against the live list.
# if the user shows offline and is in the life list then we kick them off the live list.


load_dotenv()

class TwitchManager(commands.Cog, name="TwitchManager Cog"):

    def __init__(self, bot: commands.bot):
        
        self.bot = bot
        self.twitch = Twitch(os.getenv("TWITCH_CLIENT"), os.getenv("TWITCH_SECRET"))

        self.userCheckList = []    # list of users to check for also maintains discord member id [(twitch_name, discord_member_id)]
        self.liveList = []      # list of tuples [(user, start_time)] TEMPORARY LIST FOR


    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)       
    async def twitchadd(self, ctx:commands.Context, member, username):
        
        userDict = self.twitch.get_users(logins = [username])
        userList = userDict['data']

        guild = ctx.guild

        if len(userList) > 0:   # at least 1 user exists
            oneUserDict = userList[0]
            twitchLogin = oneUserDict['display_name']
        else:
            await ctx.send("Twitch username does not exist")

    @commands.command(pass_context=True)
    async def printMember(self, ctx:commands.Context, member):
        print(member)
        print(type(member))


        


    # user_logins = ['officertfist', 'psillishaman'] # list of twitch users to check for
    # live_list = []  # list of tuples [(user, start_time)]


    # Twitch.get_streams(None, None, None, 20, None, None, user_ids, user_logins)

# twitch = Twitch(os.getenv("TWITCH_CLIENT"), os.getenv("TWITCH_SECRET"))
# # streams = twitch.get_streams(first = 1, user_login = user_logins)
# user = twitch.get_users(logins = ['asdifhjwoih2'])

# pprint(user)



    # streams is a dict which looks like:
    #
    # {'data' : [{
    #               'game_name' : 'gamename',
    #               'started_at' : '2022-04-13T20:00:27Z',
    #               'title' : 'stream title',
    #               'type' : 'live',
    #               'user_id' : '18587270',
    #               'user_login' : 'day9tv',
    #               'user_name' : 'Day9tv',
    #               '...' : '...' 
    #            }],
    #  'pagination' : {}}

    # a link to the stream should look like
    # https://www.twitch.tv/{user_login}

async def setup(bot: commands.Bot):
    await bot.add_cog(TwitchManager(bot))