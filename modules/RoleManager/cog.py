from pydoc import describe
import discord
from discord import app_commands
from discord.ext import commands

import re
import json
import emoji

# Create an object which is the name of the guild
# save the contents of this object then write them back when the bot restarts
# 
# Data members:
#   Message IDs <list>
#   Emojis to listen for <list <list>> an adjacency list which matches up to message IDs
#
# some error handling to watch out for:
#   : should check if a message id still exists in a server before doing anything. If it doesnt exist and its in the list than we should remove it from the list
#   : along with this also remove it from the listenfor list

# JSON TIP :: ALL DICT KEYS WILL NEED TO BE A STRING

#   TODO
#   - remove role on remove emoji
#   - roleadd -> if a duplicate emoji is trying to be used make sure its not on the same message
#                   -> this might need some tweaking?
#   - rolesetchannel -> start implementation
#   - create list of guild objects, each guild object holds that corresponding guilds data -> this is not very important considering this is only intended to run on 1 server. Good practice though

class RoleManager(commands.Cog, name="Role Manager Cog"):

    def __init__(self, bot: commands.Bot):
        
        self.bot = bot
        # self.channelId = 826123311758442516 <- feature deprecated due to complexity
        self.msg_role_dict = {}    # nested dictionary, maps message ids to a dict of reactions and roles which it listens for
                                    #
                                    # looks like this
                                    # dict = { msg_id : { react : role_id
                                    #                     react : role_id
                                    #                     react : role_id},
                                    #          msg_id : {...},
                                    #          msg_id : {...}
                                    #        }
                                    #

    # Create a new embed template which we can add to
    # @app_commands.command(
    #     name="roleinit",
    #     description="Initializes and embed which we can add role choices to"
    # )
    # @app_commands.describe(
    #     hex="Hex color code",
    #     title="Title for embed header"
    # )
    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)       
    async def roleinit(self, ctx:commands.Context, hex, *title):
        """
        !roleinit hex, title

        takes hex which is in format #FFFFFF and a Title for a new embed which will be the interface for the role manager
        start the process of creating a block which we can add reacts to - to assign roles
        """

        channelObj = ctx.channel
        # if channelObj == None:
        #     print("Default channel set doesn't exist - please setup a new channel")
        #     await channelObj.send(f"Default channel with ID {self.channelId} does not exist - set a new channel with !rolesetchannel")
        #     return

        try:
            regex = "^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
            p = re.compile(regex)

            if not re.search(p, hex) or hex == None or len(hex) < 7:            # check to make sure the hex passed is a valid hex code
                print("Invalid hex passed to !roleinit")
                await channelObj.send(f"Hex color code {hex} passed to cmd roleinit is invalid (correct format: #FFFFFF)")
                return
            else:
                hex = hex.split('#', 1)
                hex = hex[1]
                print(hex)
        except Exception as e:
            print(e)
        
        if not self.msg_role_dict:         # dictionary is empty, make sure theres no data to load first
            self.loadObj(ctx)

        try:
            hexCode = int(hex, 16)          # convert hex to base 16 int for embed color
        except ValueError as ve:
            print(ve)
            hexCode = 0xFFFFFF              # as a precaution in case we get past this point

        title = " ".join(title)             # gets rid of title as a list and makes it one string
        embed = discord.Embed(              # create a discord embed message
            title=f"{title}",
            description=f"",
            color=hexCode,
        )
        #                                                               # edit the embed object to contain message id in the footer
        msg = await channelObj.send(embed=embed)                        # send the template embed and get an object for pulling info from
        msgId = msg.id                                                  # message id from this embed
        embed.set_footer(text="my id: " + str(msgId))                   # add the message id to the footer of the embed which will be used for adding roles
        await msg.edit(embed=embed)                                     # edit the embed with the new footer, we do this after since the message id doesnt exist until the object is sent
        
        if msgId is not None:                                           # check if the embed message id is valid
            self.msg_role_dict[str(msgId)] = {}                             # a nested dict
            self.writeObj(ctx)                                          # write to json for future use
        else:
            await channelObj.send(f"Message id for new embed generated by !roleinit not a valid message id")

    # THESE IMPLEMENT SLASH COMMANDS BUT HONESTLY THIS IS ANNOYING
    # @app_commands.command(
    #     name="roleSetDesc",
    #     description="Set the description of a message embed used for role selection"
    # )
    # @app_commands.describe(
    #     msg_id="id of the message which contains the embed (role embeds will contain this in the footer)",
    #     descr="Description string to display"
    # )
    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)       # make sure the person executing has permissions
    async def roleSetDesc(self, ctx: commands.Context, msg_id, *descr):

        msg = await ctx.fetch_message(msg_id)

        if msg is not None:
            embed = msg.embeds[0]                               # get the fetched message as an embed object
        
        if embed is not None:
            desc = " ".join(descr)                              # update the description accordingly                
            embedDict = embed.to_dict()                         # convert from dictionary, edit, then back to dictionary
            embedDict['description'] = desc
            new_embed = embed.from_dict(embedDict)

            try:
                await msg.edit(embed=new_embed)                 # send back the edit for the description                        
            except Exception as e:
                print(e)

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)       # make sure the person executing has permissions
    async def roleadd(self, ctx: commands.Context, msg_id, at_role, react, *identifier_msg):
        """
        !roleadd messageid @role :emoji: role_name_or_message
        """

        if not self.msg_role_dict:                                             # dictionary is empty, make sure theres no data to load first
            self.loadObj(ctx)

        channelObj = ctx.channel
        msgId = str(msg_id)

        #                                                                        # role gets passed like <@&932015848489623682>
        #                                                                        # these two splits isolate the digit string
        at_role_split = at_role.split("&", 1)                                    # split from &
        at_role_split = at_role_split[1].split(">", 1)                           # split from >
        role_id = at_role_split[0]                                               # role id is at 0
        role_id = int(role_id)                                                   # convert role id from string to int

        role = discord.utils.find(lambda r: r.id == role_id, ctx.guild.roles)    # check if the role exists in the server first

        if role is None:
            print("This role was not found")
            return
       
        print(msgId)

        if msgId not in self.msg_role_dict:                               # update the message role dictionary
            print(f"The key for msg_id: {msg_id} was not found in the dictionary for role mapping. . .")
            await channelObj.send(f"The key for msg_id: {msg_id} was not found in the dictionary for role mapping. . .")
        else:
            if react in self.msg_role_dict[msgId]:
                print(f"Reaction {react} already used for this message, use a different emoji for this role. . .")
                await channelObj.send(f"Reaction {react} already used for this message, use a different emoji for this role. . .")
            else:
                emojiKey = emoji.demojize(react)                            # will return a reaction as :hundred_points: or <:Gz:829805460503789630>\
                msgIdKey = msgId

                try:
                    msg = await ctx.fetch_message(msg_id)
                    embed = msg.embeds[0]                               # get the fetched message as an embed object
                    role_msg = " ".join(identifier_msg)                 # join the identifier message as a single string
                    embed.add_field(name=f"@{role.name}", value=f"{react} - {role_msg}", inline=False)
                    await msg.edit(embed=embed)
                    await msg.add_reaction(react)                           # add the reaction
                    # await msg.edit(embed=new_embed)                         # send back the edit for the description                        
                    self.msg_role_dict[msgIdKey][emojiKey] = role_id       # add the react and role id to the dictionary indexed at the message id
                    self.writeObj(ctx)                                      # finally write the dictionary to a json file for safe keeping
                except Exception as e:
                    print(e)

    # @commands.command(pass_context=True)
    # @commands.has_permissions(administrator=True)       # make sure the person executing has permissions
    # async def rolesetchannel(self, ctx: commands.Context, channel):
    #     """
    #     !rolesetchannel #channel_name
    #     """
    #     # split off channel input to isolate the id
    #     channel_split = channel.split("#", 1)
    #     if len(channel_split) > 1:
    #         channel_split = channel_split[1].split(">", 1)
    #         channel_id = channel_split[0]
    #     else:
    #         print("Invalid channel provide")
    #         await ctx.channel.send("RoleManager: Error: use a text channel to set a role channel")
    #         return

    #     guild = ctx.guild

    #     if (lambda c: c.id == channel_id, guild.text_channels):
    #         self.channelId = channel_id
    #         await ctx.channel.send("RoleManager: channel successfully set!")
    #     else:
    #         await ctx.channel.send("RoleManager: Error: channel selected does not exist, try another.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        if payload.member == self.bot.user:
            print("Ignored bot adding emoji")
            return

        guild_id = payload.guild_id         # get the guild id so we know which file to open

        if not self.msg_role_dict:         # dictionary is empty
            try:                            # try to load the dictionary from the json file
                with open(f'modules/RoleManager/dat/{guild_id}.json') as f:
                    self.msg_role_dict = json.load(f)
                    print(self.msg_role_dict)
                    print(f"msg_role_dict loaded as: {type(self.msg_role_dict)}")
            except FileNotFoundError as fe:
                print(fe)
        
        msgId = str(payload.message_id)
        
        if msgId in self.msg_role_dict:                    # check if the message is in the dict
            reaction = str(payload.emoji)                   # reaction in form <:surprisedpikachu:899462891445559356> or 😭, which is the key to our role id
            reaction = emoji.demojize(reaction)             # demojize to turn 😭 into :sad: which is a key for default emoji : roles
            roleId = self.msg_role_dict[msgId][reaction]

            guild = self.bot.get_guild(guild_id)
            role = guild.get_role(roleId)

            for r in payload.member.roles:
                if r == role:                                       # check if the user reacting already has the role assigned, if they do, do nothing
                    print("member already assigned this role")
                    return

            await payload.member.add_roles(role)
            print("role added to member")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):

        if payload.member == self.bot.user:
            print("Ignored bot removing emoji")
            return

        guild_id = payload.guild_id

        if not self.msg_role_dict:
            try:                            # try to load the dictionary from the json file
                with open(f'modules/RoleManager/dat/{guild_id}.json') as f:
                    self.msg_role_dict = json.load(f)
                    print(self.msg_role_dict)
                    print(f"msg_role_dict loaded as: {type(self.msg_role_dict)}")
            except FileNotFoundError as fe:
                print(fe)

        msgId = str(payload.message_id)
        if msgId in self.msg_role_dict:
            userId = payload.user_id

            guild = self.bot.get_guild(guild_id)
            member = guild.get_member(userId)

            reaction = str(payload.emoji)
            reaction = emoji.demojize(reaction)

            if reaction in self.msg_role_dict[msgId]:
                role_id = self.msg_role_dict[msgId][reaction]
                role = guild.get_role(role_id)
                for r in member.roles:
                    if r == role:
                        await member.remove_roles(role)
                        return
            else:
                print("Emoji not found as a key in this msgId")
        else:
            print("msgId not found")
                


    # load data from a file, json
    def loadObj(self, ctx):

        #guild_id = ctx.message.guild.id
        guild_id = ctx.message.guild.id

        try:
            with open(f'modules/RoleManager/dat/{guild_id}.json') as f:
                self.msg_role_dict = json.load(f)
        except FileNotFoundError as fe:
            print(fe)


    # write object data to a file, json
    def writeObj(self, ctx):
    
        #guild_id = ctx.message.guild.id
        guild_id = ctx.message.guild.id
        
        try:
            with open(f'modules/RoleManager/dat/{guild_id}.json', 'w') as f:
                f.write(json.dumps(self.msg_role_dict))
        except FileNotFoundError as fe:
            print(fe)

async def setup(bot: commands.Bot):
    await bot.add_cog(RoleManager(bot), guilds=[discord.Object(id=633847600403054592)])
