# BakeryBot

## The discord bot for the server, "The Bakery"

### Purpose
The purpose of the bot is to help with moderation, role managment, and implement fun tools. Development started to replace already
existing bots which we used in the server and consolidate them by recreating their functionality using unique code.

### Use
In order to compile and run this bot you need to use a unique token which is generated by the discord bot API. This is stored in
an environment variable. To compile use a virtual environment and install the packages from requirements.txt

All commands use the prefix "!"

### Functionality
Some of the bots functionalities are listed below:
* Dice Bot
* Role Manager
* Chat Manager

### Bots

#### Roll (Dice Bot)
Commands:
* !roll xDy -> input is formatted like xDy where x is the number of dice to roll and y is the type of dice e.g. (D4, D6, D20)

#### RoleManager (Admin Only)
Commands:
* !roleinit hex title
* !rolesetdesc msg_id description
* !roleadd msg_id role emoji message

#### ChatManager (Admin Only)
Commands:
* !purge n -> removes n messages from the channel this was called in

#### Twitch Notification (Admin Only)
Commands:
* !twitchadd @member twitchUsername -> adds a member associated with a twitch name to the notification list
* !twitchremove @member -> removes a member from the notification list
* !twitchnotos  -> prints a list of everyone on the notification list
* !twitchlive -> prints a list of everyone who is currently live on twitch


### Future Plans
Some future implementations were looking at at:
* Radio
* Joke bot
* Bread bot
* Slash commands implementation