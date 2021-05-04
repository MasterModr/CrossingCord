from Config import *
from CrossingCord import *
from discord.ext import commands
from var_secrets import TOKEN

from datetime import datetime


bot = commands.Bot(command_prefix=BOT_PREFIX)

# Checking folders exist
if not os.path.isdir("IO Files/"):
    print("Creating IO Files folder...")
    os.makedirs("IO Files")


@bot.event
async def on_ready():
    print('\nLogged in as ' + bot.user.name + "(ID: " + str(bot.user.id) + ")")
    print('~~~~~~~~~~~~')
    cord = CrossingCord(bot)
    bot.add_cog(cord)
    print('CrossingCord Launched')
    #bot.load_extension('Commands')
    print('Commands Loaded')
    await cord.on_ready()



@bot.event
async def on_command(context):
    print("[{}]: '{}' by {}".format(datetime.now().strftime("%b-%d %H:%M"), context.command, context.author))
    pass


@bot.event
async def on_command_error(ctx, error):
    print(error)
    # print(dir(error))
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')


bot.run(TOKEN)
