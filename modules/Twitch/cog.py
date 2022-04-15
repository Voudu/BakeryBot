import os
from dotenv import load_dotenv
from twitchAPI.twitch import Twitch
from discord.ext import commands, tasks
import discord
import random
import json
from pprint import pprint

# SEE: https://dev.twitch.tv/docs/api/reference#get-streams

load_dotenv()

r = lambda: random.randint(0,255)       # lambda function used for generating random hex colors

class TwitchManager(commands.Cog, name="TwitchManager Cog"):

    def __init__(self, bot: commands.bot):

        self.bot = bot
        self.twitch = Twitch(os.getenv("TWITCH_CLIENT"), os.getenv("TWITCH_SECRET"))

        self.loaded = False
        self.firstStartup = True

        self.userCheckList = []     # list of users to check for also maintains discord member id [(twitch_name, discord_member_id)]
        self.liveList = []          # list of users who are live [twitch_username]

        self.promoChannelId = 643167159572234261        # CHANGE THIS ID TO THE CHANNEL YOU WANT NOTIFICATION SENT IN
        self.checkList.start()

    # #############################################################################################################
    #
    #   checkList
    #   
    #   Every 30 seconds check users on the list for members who have went live since the last check
    #
    # #############################################################################################################
    @tasks.loop(seconds=30)
    async def checkList(self):

        guild = self.bot.get_guild( int(os.getenv("GUILD_ID")) )
        if guild is None:
            return

        #
        #   check if the userCheckList has been loaded or not yet
        #
        if not self.loaded and not self.userCheckList:
            self.loadData(guild.id)             # list hasn't been loaded yet, load it
        
        #
        #   first lets check if users have the LIVE role and are not LIVE
        #   really this should only happen if the bot was interrupted on startup.
        #   only do this once to avoid constantly searching members
        #
        if not self.liveList and self.firstStartup:                               # liveList is empty, so no one should have the live role
            role = discord.utils.find(lambda rl: rl.name == "LIVE", guild.roles)  # Get the LIVE role

            # Iterate through all members of the server and see if any of there roles contain LIVE
            for member in guild.members:
                for r in member.roles:              # check all roles of each member
                    if r == role:                   # if the member has the LIVE role on first startup
                        await member.remove_roles(role)   # remove it

            self.firstStartup = False               # toggle this bool so it only happens once on startup

        # get the set channel to send notification to
        channel = self.bot.get_channel(self.promoChannelId)

        #
        #   iterate through userCheckList for possible notifcations to send
        #
        isLive = False                  # bool used to detect if a user is still live - used to avoid duplicate notifications

        for user in self.userCheckList:
            stream = self.twitch.get_streams(first = 1, user_login = [user[0]])     # pull twitch stream for a single user

            twitchUser = user[0]

            for live in self.liveList:                              # check user against all entries in liveList to see if a notification has already been sent
                if live.lower() == twitchUser.lower() and stream['data']:           # user is still live from a previous time, do not send a duplicate notification
                    isLive = True                                   # flag the user as isLive - meaning the user has been live for a while now
                elif live.lower() == twitchUser.lower() and not stream['data']:     # user who was previously live is no longer live and needs to be removed from the list
                    self.liveList.remove(live)                      # remove the user from the liveList

                    role = discord.utils.find(lambda rl: rl.name == "LIVE", guild.roles)  # find the role to add
                    member = guild.get_member( int(user[1]) )                             # get the member we need to add role to
                    if member is not None:
                        memberRole = member.get_role(role.id)
                        if memberRole is None:
                            print(f"Twitch: User {live} no longer LIVE --> Removing from live list")
                            await member.remove_roles(role)
                        # else, member doesnt have the "LIVE" role to remove
                    
            if stream['data'] and not isLive:                       # if stream data exists the user isn't already in the liveList
                streamData = stream['data'][0]                      # dictionary containing stream data
                # pprint(stream)
                self.liveList.append(streamData['user_login'])          # append the user who is now live
                print(f"Twitch: User {streamData['user_login']} LIVE --> Adding to live list")

                #
                #   Gather data from stream for creating the embed
                #
                twitchDisplayName = streamData['user_name']
                twitchGameName = streamData['game_name']
                twitchTitle = streamData['title']
                twitchUserLogin = streamData['user_login']
                streamUrl = f"https://www.twitch.tv/{twitchUserLogin}"

                # generate a random hex color
                # hexString = ('%02X%02X%02X' % (r(), r(), r()))            # didnt work as intended, removing for now
                # hexColor = int(hexString, 16)

                #
                #   Get user for extracting profile picture
                #
                userProfile = self.twitch.get_users(logins=[user[0]])
                if userProfile['data']:
                    thumbnail = userProfile['data'][0]['profile_image_url']

                #
                #   Create the embed notification
                #
                embed=discord.Embed(title=f"{twitchDisplayName} is Live!", url=streamUrl, description=twitchTitle, color=0x6441A5)
                embed.set_author(name=twitchDisplayName, url=streamUrl, icon_url=thumbnail)
                embed.set_thumbnail(url=thumbnail)
                embed.add_field(name="Streaming:", value=twitchGameName, inline=True)
                # embed.set_footer(text="Support our friends by following and dropping in to chat")     # this looked kinda bad
                
                # send the embed notifcation
                await channel.send(embed=embed)

                #
                #   Add member to the "LIVE" role
                #
                role = discord.utils.find(lambda rl: rl.name == "LIVE", guild.roles)  # find the role to add
                member = guild.get_member( int(user[1]) )                             # get the member we need to add role to
                if member is not None:
                    memberRole = member.get_role(role.id)                             # returns None if the user does not have the role
                    if memberRole is None:
                        await member.add_roles(role)

            isLive = False          # reset this flag for checking the next user
            
    # #############################################################################################################
    #
    #   !twitchadd @member twitchUsername
    #   
    #   This command associates a discord member and a twitch username and adds its to a notification list
    #
    # #############################################################################################################
    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)       
    async def twitchadd(self, ctx:commands.Context, member, username):
        
        guild = ctx.guild
        
        #
        #   Load data to json if it hasnt yet
        #
        if not self.userCheckList and not self.loaded:
            self.loadData(ctx.guild.id)

        # 
        #   First parse member input
        #
        try:
            split = member.split('@', 1)     # remove <@ from member string
            split = split[1].split('>', 1)   # remove > from end of member string
            memberId = int( split[0] )       # isolate member id, store as int
        except Exception as e:
            await ctx.send("Member input was invalid")
            return

        member = await guild.fetch_member(memberId)     # fetch member object from id
        if member is None:                        # member doesnt exists in guild
            await ctx.send("Member provided does not exist in guild")
            return

        #
        #   Now parse twitch username input
        #
        userDict = self.twitch.get_users(logins = [username])
        userList = userDict['data']

        if len(userList) > 0:               # at least 1 user exists
            oneUserDict = userList[0]
            twitchLogin = oneUserDict['display_name']
        else:
            await ctx.send("Twitch username does not exist")
            return
        
        # check if the list contains either this member or twitch already
        for tuple in self.userCheckList:
            if tuple[0] == twitchLogin or tuple[1] == memberId:
                await ctx.send("Twitch username or Member already associated in this guild. Not adding to notification list")
                return

        #
        #   Now we have memberId and twitchLogin -> build tuple, insert into userCheckList
        # 
        memberTuple = (twitchLogin, memberId)       # create a new tuple (twitchLogin, memberId)
        self.userCheckList.append(memberTuple)      # append to userCheckList
        await ctx.send(f"Added {memberId} to twitch notification list")
        
        self.writeData(ctx.guild.id)                         #   Finally we save the new list to a .json file for accessing later

    # #############################################################################################################
    #
    #   !twitchremove @member
    #   
    #   Removes a member from the notifcation list given they're on the list
    #
    # #############################################################################################################
    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def twitchremove(self, ctx:commands.Context, member):
        
        # guild = ctx.guild

        #
        #   Load data to json if it hasn't yet
        #
        if not self.userCheckList and not self.loaded:
            self.loadData(ctx.guild.id)

        # 
        #   parse member input
        #
        split = member.split('@', 1)     # remove <@ from member string
        split = split[1].split('>', 1)   # remove > from end of member string
        memberId = int( split[0] )       # isolate member id, store as int
        memberObj = ctx.guild.get_member(memberId)

        #
        #   check if the member we removed had the LIVE role and remove it from them if they did
        #
        role = discord.utils.find(lambda rl: rl.name == "LIVE", ctx.guild.roles)  # Get the LIVE role
        if memberObj is not None and memberObj.get_role(role.id) is not None:
            await memberObj.remove_roles(role)

        #
        #   find the member in the notification list and remove them
        #
        for user in self.userCheckList:  # check if member is in the list
            if user[1] == memberId:      # member in list
                
                # also check if this user is in the live list
                for live in self.liveList:
                    if user[0].lower() == live.lower():
                        self.liveList.remove(live)      # remove them if they were in the live list

                self.userCheckList.remove(user)
                self.writeData(ctx.guild.id)           # save the updated list
                await ctx.send(f"Removed {memberId} from twitch notifcation list")
                return                   # return on successful removal and write
        
        await ctx.send(f"Member {member} not found in the twitch notification list")

    # #############################################################################################################
    #
    #   !twitchprint
    #   
    #   Prints a list of members on the twitch notification list
    #
    # #############################################################################################################
    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def twitchnotos(self, ctx:commands.Context):
        
        header = "Users on the automatic twitch notifcation list: \n\n"
        userStrings = []

        guild = ctx.guild

        i = 1
        for user in self.userCheckList:
            member = guild.get_member(int(user[1]))
            userStrings.append(f"{i}. @{member.name}    |   twitch name: {user[0]}")
            i=i+1

        body = "\n".join(userStrings)

        await ctx.send(header + body)

    # #############################################################################################################
    #
    #   !twitchlive
    #   
    #   Prints a list of members currently live on twitch
    #
    # #############################################################################################################
    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def twitchlive(self, ctx:commands.Context):
        
        header = "User currently live on twitch: \n\n"
        userStrings = []

        i = 1
        for user in self.liveList:
            userStrings.append(f"{i}. twitch.tv/{user}")

        body = "\n".join(userStrings)

        await ctx.send(header + body)

    # load notification list data from json to list
    def loadData(self, guildId):
        guildId = str(guildId)

        try:
            with open(f'modules/Twitch/dat/{guildId}.json') as f:
                self.userCheckList = json.load(f)
            self.loaded = True
            print("Loaded Twitch data")
        except FileNotFoundError as fe:
            self.writeData(guildId)         # if the file doesn't exist we should make it
            print(fe)

    # write notification list data to json
    def writeData(self, guildId):
        guildId = str(guildId)

        try:
            with open(f'modules/Twitch/dat/{guildId}.json', 'w') as f:
                f.write(json.dumps(self.userCheckList))
            print("Saved Twitch data")
        except FileNotFoundError as fe:
            print(fe)

async def setup(bot: commands.Bot):
    await bot.add_cog(TwitchManager(bot))