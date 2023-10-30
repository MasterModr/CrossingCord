import asyncio
import os
import random
import sys
import urllib
import time as t
from datetime import timedelta
from io import BytesIO

import discord
import base64
import mysql.connector as mysql
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands
from Config import *
from Util.Weather import *


class CrossingCord(commands.Cog):

    baseurl = "http://ec2-52-6-191-118.compute-1.amazonaws.com/assets"
    guarantee_shiny = False
    spawn_min = 30
    spawn_max = 60
    spawn_list = []

    def __init__(self, bot):
        self.bot = bot
        self.time_to_spawn = None
        self.villager_store = None
        self.db = mysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER_NAME,
            passwd=MYSQL_PASS,
            database=MYSQL_DATABASE
        )
        self.update_spawn_rates()
        self.update_weather()

    @property
    def appeared(self):
        return self.villager_store is not None

    @property
    def time_to_spawn(self):
        return self._time_to_spawn

    @time_to_spawn.setter
    def time_to_spawn(self, value):
        self._time_to_spawn = value

    def getSeconds(self):
        return (self.time_to_spawn - datetime.now()).total_seconds()

    def setToSpawn(self):
        if self.time_to_spawn is None:
            return False
        else:
            return True

    @setInterval(60)
    def update_weather(self):
        weather = get_weather()
        print(weather['time'])
        hour = int(weather['time'].split(":")[0])
        cursor = self.db.cursor()
        if 200 <= weather['id'] <= 699:
            query = (
                f"UPDATE villagers "
                "SET rate = 10 "
                f"WHERE id = 404")
        else:
            query = (
                f"UPDATE villagers "
                "SET rate = 0 "
                f"WHERE id = 404")
        cursor.execute(query)

        if weather['id'] == 800 and (hour >= 18 or hour <= 5 ):
            query = (
                f"UPDATE villagers "
                "SET rate = 5 "
                f"WHERE id = 405")
        else:
            query = (
                f"UPDATE villagers "
                "SET rate = 0 "
                f"WHERE id = 405")

        cursor.execute(query)
        self.db.commit()
        cursor.close()
        self.update_spawn_rates()

    def update_spawn_rates(self):
        temp_list = []
        cursor = self.db.cursor()
        cursor.execute("SELECT id, rate from villagers")
        for id, rate in cursor.fetchall():
            temp_list += [id] * rate
        self.spawn_list = temp_list

    async def helper_perms(self):
        for role in self.author.roles:
            if HELPER_ROLE == role.id:
                return True
        return False

    async def admin_perms(self):
        if self.author.id in ADMIN_IDS:
            return True
        else:
            return False

    @commands.command(name='updaterates')
    @commands.is_owner()
    async def cmd_updaterates(self, context, message=None):
        self.update_spawn_rates()
        await context.channel.send("Spawn Rates have been updated.")

    @commands.command(name='weather')
    async def cmd_weather(self, context, message=None):
        weather = get_weather()
        embed = discord.Embed(type="rich", title="Weather")
        embed.description = f"The weather at {weather['time']} in Moonbeam is {weather['description']}"
        embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{weather['icon']}@2x.png")
        await context.channel.send(embed=embed)

    async def draw_island(self, context):
        dict_cursor = self.db.cursor(dictionary=True)
        dict_cursor.execute(
            "SELECT * "
            "FROM islands "
            f"WHERE discord_id LIKE {context.author.id};")
        row = dict_cursor.fetchone()
        if row is not None:
            cursor = self.db.cursor()
            image = Image.open('assets/Images/island.png')
            draw = ImageDraw.Draw(image)
            if row['background'] is not None:
                try:
                    background = Image.open(BytesIO(requests.get(row['background']).content))
                    background = background.resize((700, 375), Image.ANTIALIAS)
                    image.paste(background, (0, 0), image)
                    slots = Image.open('assets/Images/slots.png')
                    image.paste(slots, (0, 0), slots)
                except:
                    await self.islandremovebackground(context)

            font = ImageFont.truetype('assets/Fonts/FinkHeavy.ttf', size=45)
            (x, y) = (75, 50)
            username = context.author.name
            if len(username) > 13:
                message = username[:10] + "...'s Island."
            else:
                message = username + "'s Island."

            color = 'rgb(0, 0, 0)'  # black color
            draw.text((x, y), message, fill=color, font=font)

            cursor.execute(
                "SELECT captures.number, captures.shiny_number, villagers.name "
                "FROM captures "
                "INNER JOIN villagers ON captures.villager_id = villagers.id "
                "INNER JOIN users ON captures.user_id = users.id "
                f"WHERE users.discord_id LIKE {context.author.id};")
            results = cursor.fetchall()
            user_list = {}
            for number, shiny_number, name in results:
                user_list[name] = [number, shiny_number]
            xcoord = 50
            ycoord = 112
            i = 0
            while i < 10:
                villager = row[f"villager{i + 1 }"]
                if villager is not None:
                    cursor.execute(f"SELECT name from villagers WHERE id = {villager};")
                    name = cursor.fetchone()[0]
                    response = requests.get("{}/icon/{}.png".format(self.baseurl, name))
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((100, 100), Image.ANTIALIAS)
                    image.paste(img, (xcoord, ycoord), img)
                    if user_list[name][1] >= 1:
                        print(name)
                        sparkle = Image.open('assets/Images/sparkles.png')
                        image.paste(sparkle, (xcoord + 10, ycoord + 70), sparkle)
                    if user_list[name][0] >= 100:
                        star = Image.open('assets/Images/gold.png')
                        image.paste(star, (xcoord + 70, ycoord + 70), star)
                    elif user_list[name][0] >= 50:
                        star = Image.open('assets/Images/silver.png')
                        image.paste(star, (xcoord + 70, ycoord + 70), star)
                    elif user_list[name][0] >= 10:
                        star = Image.open('assets/Images/bronze.png')
                        image.paste(star, (xcoord + 70, ycoord + 70), star)

                    if i == 4:
                        xcoord = 50
                        ycoord = 237
                    else:
                        xcoord += 125
                i = i + 1
            fp = BytesIO()
            image.save(fp, format="PNG")
            fp.seek(0)
            dict_cursor.close()
            cursor.close()
            await context.channel.send(file=discord.File(fp, 'island.png'))
        else:
            await context.channel.send("```\nYou do not have an island please add Villagers first.\n```")

    async def on_ready(self):
        print("Listening")
        channel = self.bot.get_channel(CHANNEL)
        message = await channel.send("PokeCord Started.")
        await self._spawn(message)
        # Check if a pokemon is queued to be spawned
        """if self.setToSpawn():
            # If time to spawn in the future set in motion
            if self.time_to_spawn > datetime.now():
                await asyncio.sleep(self.getSeconds())
            # await self.cmd_spawn('spawn', client.get_channel(CHANNEL_IDs))"""

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bot or wrong channel do nothing
        if message.author == self.bot.user or message.content[1:].startswith(
                "spawn"):  # or message.channel == CHANNEL_IDs:
            return

        # Pokemon is going to be found
        if self.setToSpawn():
            pass
        else:
            # Pokemon is ready for capture
            if self.appeared:
                await self.check_capture(message)

    @commands.command(name='restart')
    @commands.check(helper_perms)
    async def cmd_restart(self, ctx, message=None):
        await ctx.channel.send('Restarting...')
        await self.bot.close()
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command(name='total')
    @commands.is_owner()
    async def cmd_total(self, context):
        cursor = self.db.cursor()
        cursor.execute("SELECT number from crossingcord.captures")
        results = cursor.fetchall()
        total = 0
        for result in results:
            total += int(result[0])
        await context.channel.send(f"Total Villagers Caught: {total}")

    @commands.command(name='inventory')
    async def cmd_inventory(self, context):
        cursor = self.db.cursor()
        cursor.execute(f"SELECT id from users WHERE discord_id = {context.author.id};")
        result = cursor.fetchone()
        if result is not None:
            str_title = "{}'s Villagers".format(context.author.name)
            embed = discord.Embed(type="rich", title=str_title, color=0xEEE8AA)

            embed.description = "http://pokecord.meganisaclown.com/villagers/villager.php?name={}&id={}" \
                .format(urllib.parse.quote(base64.b64encode(context.author.name.encode('ascii'))), context.author.id)
            await context.channel.send(embed=embed)
        else:
            msg = "{} you have no Villagers".format(context.author.name)
            await context.channel.send(msg)

    @commands.command(name='shutdown')
    @commands.is_owner()
    async def cmd_shutdown(self, context):
        await self.bot.close()
        # exit()

    @commands.command(name='startspeedround')
    @commands.check(admin_perms)
    async def cmd_startspeedround(self, context):
        await self.startHypeTrain(context)
        # exit()

    async def startHypeTrain(self, context):
        self.traintime = t.time() + 10800
        await context.channel.send("{} triggered a Speed Round it Will Begin Shortly!".format(context.author.name))
        oldmin = self.spawn_min
        oldmax = self.spawn_max
        self.spawn_min = 2
        self.spawn_max = 5
        await asyncio.sleep(180)
        await self.stopHypeTrain(context, oldmin, oldmax)

    async def stopHypeTrain(self, context, oldmin, oldmax):
        self.spawn_min = oldmin
        self.spawn_max = oldmax
        await context.channel.send("The Speed Round is over hope you had fun!")

    async def islandexists(self, context):
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * "
            "FROM islands "
            f"WHERE discord_id LIKE {context.author.id};"
        )
        row = cursor.fetchone()
        cursor.close()
        if row is not None:
            return True
        else:
            return False

    async def islandremovebackground(self, context):
        cursor = self.db.cursor()
        query = (
            "UPDATE islands "
            "SET background = NULL "
            f"WHERE discord_id = '{context.author.id}';")
        cursor.execute(query)
        self.db.commit()

    async def islandreplace(self, context, villager, villager1):
        dict_cursor = self.db.cursor(dictionary=True)
        dict_cursor.execute(
            "SELECT villager1, villager2, villager3, villager4, villager5, villager6, villager7, villager8, villager9, villager10 "
            "FROM islands "
            f"WHERE discord_id = '{context.author.id}';"
        )
        row = dict_cursor.fetchone()
        new_cursor = self.db.cursor()
        new_cursor.execute(f"SELECT id FROM villagers WHERE villagers.name = '{villager.title()}';")
        result = new_cursor.fetchone();
        vil_id = result[0]
        if row is not None:
            island = list(row.values())
            if vil_id in island:
                new_cursor.execute(f"SELECT id FROM villagers WHERE villagers.name = '{villager1.title()}';")
                result = new_cursor.fetchone();
                vil1_id = result[0]
                island[island.index(vil_id)] = vil1_id
                query = (
                    "UPDATE islands "
                    f"SET villager1 = {island[0]}, villager2 = {island[1]}, villager3 = {island[2]}, "
                    f"villager4 = {island[3]}, villager5 = {island[4]}, villager6 = {island[5]}, "
                    f"villager7 = {island[6]}, villager8 = {island[7]}, villager9 = {island[8]}, villager10 = {island[9]} "
                    f"WHERE discord_id LIKE {context.author.id};"
                )
                query = query.replace("None", "NULL")
                cursor = self.db.cursor()
                cursor.execute(query)
                self.db.commit()
                await context.channel.send("```\n{} has been replaced with {} on your island.\n```".format(villager.title(), villager1.title()))
            else:
                await context.channel.send("```\n{} is not on your island.\n```".format(villager.title()))
        else:
            await context.channel.send("```\nYou do not have an island please add Villagers first.\n```")

    async def islandadd(self, context, villager):
        dict_cursor = self.db.cursor(dictionary=True)
        dict_cursor.execute(
            "SELECT villager1, villager2, villager3, villager4, villager5, villager6, villager7, villager8, villager9, villager10 "
            "FROM islands "
            f"WHERE discord_id = '{context.author.id}';"
        )
        row = dict_cursor.fetchone()
        if row is not None:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT villagers.name, villagers.id "
                "FROM captures "
                "INNER JOIN villagers ON captures.villager_id = villagers.id "
                "INNER JOIN users ON captures.user_id = users.id "
                f"WHERE users.discord_id LIKE {context.author.id};"
            )
            results = cursor.fetchall()
            if len(results) > 0:
                user_list = {}
                for name, id in results:
                    user_list[name.lower()] = [name, id]
                if villager.lower() in user_list.keys():
                    island = list(row.values())
                    if user_list[villager.lower()][1] not in island:
                        i = 0
                        added = False
                        while i < 10:
                            if island[i] is None:
                                query = (
                                    f"UPDATE islands "
                                    f"SET villager{i + 1} = {user_list[villager.lower()][1]} "
                                    f"WHERE discord_id = {context.author.id};"
                                )
                                cursor.execute(query)
                                self.db.commit()
                                added = True
                                break;
                            i = i+1
                        if added:
                            await context.channel.send("```\n{} has been added to your island.\n```".format(villager.title()))
                        else:
                            await context.channel.send("```\nYou do not have space on your island.\n```")
                    else:
                        await context.channel.send("```\n{} is already on your island.\n```".format(villager.title()))
                else:
                    await context.channel.send("```\nYou have not found {}.\n```".format(villager.title()))
            else:
                await context.channel.send("```\nYou have not found any Villagers.\n```")
        else:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT villagers.name, villagers.id "
                "FROM captures "
                "INNER JOIN villagers ON captures.villager_id = villagers.id "
                "INNER JOIN users ON captures.user_id = users.id "
                f"WHERE users.discord_id LIKE {context.author.id};"
            )
            results = cursor.fetchall()
            if len(results) > 0:
                user_list = {}
                for name, id in results:
                    user_list[name.lower()] = [name, id]
                if villager.lower() in user_list.keys():
                    cursor.execute(
                        f"INSERT INTO islands (discord_id, villager1) VALUES ({context.author.id}, {user_list[villager.lower()][1]});"
                    )
                else:
                    await context.channel.send("```\nYou have not found {}.\n```".format(villager.title()))
            else:
                await context.channel.send("```\nYou have not found any Villagers.\n```")



    async def islandrm(self, context, villager):
        dict_cursor = self.db.cursor(dictionary=True)
        dict_cursor.execute(
            "SELECT villager1, villager2, villager3, villager4, villager5, villager6, villager7, villager8, villager9, villager10 "
            "FROM islands "
            f"WHERE discord_id = '{context.author.id}';"
        )
        row = dict_cursor.fetchone()
        new_cursor = self.db.cursor()
        new_cursor.execute(f"SELECT id FROM villagers WHERE villagers.name = '{villager.title()}';")
        result = new_cursor.fetchone();
        vil_id = result[0]
        if row is not None:
            island = list(row.values())
            if vil_id in island:
                island.remove(vil_id)
                query = (
                    "UPDATE islands "
                    f"SET villager1 = {island[0]}, villager2 = {island[1]}, villager3 = {island[2]}, "
                    f"villager4 = {island[3]}, villager5 = {island[4]}, villager6 = {island[5]}, "
                    f"villager7 = {island[6]}, villager8 = {island[7]}, villager9 = {island[8]}, villager10 = None "
                    f"WHERE discord_id LIKE {context.author.id};"
                )
                query = query.replace("None", "NULL")
                cursor = self.db.cursor()
                cursor.execute(query)
                self.db.commit()
                await context.channel.send("```\n{} has been removed from your island.\n```".format(villager.title()))
            else:
                await context.channel.send("```\n{} is not on your island.\n```".format(villager.title()))
        else:
            await context.channel.send("```\nYou do not have an island please add Villagers first.\n```")

    async def islandbackground(self, context, background):
        cursor = self.db.cursor()
        query = (
            f"UPDATE islands "
            f"SET background = '{background}'"
            f"WHERE discord_id = {context.author.id};")
        cursor.execute(query)
        self.db.commit()

    @commands.command(name='odds')
    async def cmd_odds(self, context):
        embed = discord.Embed(title="__**Shiny Odds:**__",
                              description="**Non-Sub:** 1/2048\n**Tier 1 Sub:** 1/1024\n**Tier 2 Sub:** 1/512\n**Discord Boosters:** 1/512\n**Tier 3 Sub:** 1/256\n")
        await context.channel.send(embed=embed)

    @commands.command(name='island')
    async def cmd_island(self, context, *args):
        # no arguments supplied
        text = ""
        if len(args) == 0:
            await self.draw_island(context)
        else:
            if args[0] == 'help':
                if len(args) == 1:
                    text = ""
                    text += "```\n"
                    text += "Island Commands:\n"
                    text += "   add: Adds a Villager to your Island.\n"
                    text += "   remove: Removes a Villager from your Island.\n"
                    text += "   replace: Replaces a villager on your Island.\n"
                    text += "   setbackground: Sets your Island's background.\n"
                    text += "   removebackground: Removes your Island's background.\n"
                    text += "   help: This message.\n"
                    text += "\n"
                    text += "You can also do ;island help [command] for more info.\n"
                    text += "```\n"
                    await context.channel.send(text)
                else:
                    if args[1] == 'add':
                        text = ""
                        text += "```\n"
                        text += "Island Add:\n"
                        text += "   format: ;island add [villager]"
                        text += "\n"
                        text += "Adds a villager to your Island. This must be a villager you have already found. And you cannot exceed 10 villagers on your Island.\n"
                        text += "```\n"
                        await context.channel.send(text)
                    elif args[1] == 'remove':
                        text = ""
                        text += "```\n"
                        text += "Island Remove:\n"
                        text += "   format: ;island remove [villager]"
                        text += "\n"
                        text += "Removes a villager from your Island.\n"
                        text += "```\n"
                        await context.channel.send(text)
                    elif args[1] == 'replace':
                        text = ""
                        text += "```\n"
                        text += "Island Replace:\n"
                        text += "   format: ;island replace [villager1] [villager2]"
                        text += "\n"
                        text += "Replaces a villager on your Island, villager1 is the villager that is currently on yout Island and villager2 is the villager you would like to replace them with.\n"
                        text += "```\n"
                        await context.channel.send(text)
                    elif args[1] == 'setbackground':
                        text = ""
                        text += "```\n"
                        text += "Island SetBackground:\n"
                        text += "   format: ;island setbackground [link]"
                        text += "\n"
                        text += "Sets your Island's background to the provided image.\n"
                        text += "The provided link must be a .png file."
                        text += "```\n"
                        await context.channel.send(text)
                    elif args[1] == 'removebackground':
                        text = ""
                        text += "```\n"
                        text += "Island RemoveBackground:\n"
                        text += "Removes your Island's background and sets it back to the default image."
                        text += "```\n"
                        await context.channel.send(text)
                    elif args[1] == 'help':
                        text = ""
                        text += "```\n"
                        text += "Island Help:\n"
                        text += "Think you're being funny don't ya?"
                        text += "```\n"
                        await context.channel.send(text)
                    else:
                        text = ""
                        text += "```\n"
                        text += "Unrecognized Command\n"
                        text += "```\n"
                        await context.channel.send(text)
            elif args[0] == 'add':
                if len(args) == 1:
                    text = ""
                    text += "```\n"
                    text += "Please specify a villager.\n"
                    text += "```\n"
                    await context.channel.send(text)
                else:
                    await self.islandadd(context, args[1])
            elif args[0] == 'remove':
                if len(args) == 1:
                    text = ""
                    text += "```\n"
                    text += "Please specify a villager.\n"
                    text += "```\n"
                    await context.channel.send(text)
                else:
                    await self.islandrm(context, args[1])
            elif args[0] == 'replace':
                if len(args) < 3:
                    text = ""
                    text += "```\n"
                    text += "Please specify two villagers.\n"
                    text += "```\n"
                    await context.channel.send(text)
                else:
                    await self.islandreplace(context, args[1], args[2])
            elif args[0] == 'setbackground':
                if len(args) == 1:
                    text = ""
                    text += "```\n"
                    text += "Please provide a background link.\n"
                    text += "```\n"
                    await context.channel.send(text)
                else:
                    if await self.islandexists(context):
                        if args[1][-4:] == ".png":

                            await self.islandbackground(context, args[1])
                            text = ""
                            text += "```\n"
                            text += "Your background has been updated.\n"
                            text += "```\n"
                            await context.channel.send(text)
                        else:
                            text = ""
                            text += "```\n"
                            text += "The background link must be a PNG.\n"
                            text += "```\n"
                            await context.channel.send(text)
                    else:
                        text = ""
                        text += "```\n"
                        text += "You do not have an island please add Villagers first.\n"
                        text += "```\n"
                        await context.channel.send(text)

            elif args[0] == 'removebackground':
                if await self.islandexists(context):
                    await self.islandremovebackground(context)
                    text = ""
                    text += "```\n"
                    text += "Your background has been removed.\n"
                    text += "```\n"
                    await context.channel.send(text)
                else:
                    text = ""
                    text += "```\n"
                    text += "You do not have an island please add Villagers first.\n"
                    text += "```\n"
                    await context.channel.send(text)

            else:
                text = ""
                text += "```\n"
                text += "Unrecognized Command\n"
                text += "```\n"
                await context.channel.send(text)


        # exit()

    @commands.command(name='shinycheck')
    @commands.is_owner()
    async def cmd_shinycheck(self, context):
        message = ""
        for villager in self.villagerdata:
            response = requests.get("{}/shiny/{}.png".format(self.baseurl, villager[0]))
            if (response.status_code > 400):
                message = message + "{}: No\n".format(villager[0])
            else:
                message = message + "{}: Yes\n".format(villager[0])
            if (len(message) > 1500):
                await context.channel.send(message)
                message = ""
        await context.channel.send(message)

    @commands.command(name='spawn')
    @commands.is_owner()
    async def cmd_spawn(self, context, message=None):
        await self._spawn(context, message)

    @commands.command(name='setspawnrate')
    @commands.is_owner()
    async def cmd_setspawnrate(self, context, *args):
        cursor = self.db.cursor();
        query = (
            f"UPDATE villagers "
            f"SET rate = {args[1]} "
            f"WHERE name = '{args[0]}';")
        cursor.execute(query)
        self.db.commit()
        self.cmd_updaterates(context)

    async def _spawn(self, context, message=None):
        spawnnumber = 0
        if message is None:
            # spawnnumber = random.randint(0,len(self.villagerdata)-1)
            spawnnumber = random.choice(self.spawn_list)
        else:
            spawnnumber = int(message)

        cursor = self.db.cursor()
        cursor.execute(f"SELECT name, id FROM villagers WHERE id = {spawnnumber};")
        result = cursor.fetchone();
        new_data = [result[0], result[1]]
        self.time_to_spawn = None
        await context.channel.send('A Villager appears!')
        self.villager_store = new_data

        embed = discord.Embed()
        embed.title = "Who's that Villager"
        embed.set_thumbnail(url="{}/normal/{}.png".format(self.baseurl, self.villager_store[0]))
        sent_msg = await context.channel.send(embed=embed)
        self.spawn_msg = sent_msg.id
        game = discord.Game("Who's That Villager?")
        await self.bot.change_presence(status=discord.Status.online, activity=game)

    async def check_capture(self, message):
        # await self.checkTrain(message)
        pokemessage = message.content.lower().replace(" ", "_")
        if pokemessage == 'mogs':
            pokemessage = 'bertha'
        if pokemessage == 'becca':
            pokemessage = 'marcel'
        if pokemessage == 'gaia':
            pokemessage = 'becky'
        if pokemessage == 'gary':
            pokemessage = 'sly'
        if pokemessage == 'snek':
            pokemessage = 'snake'
        if pokemessage == 'coochieface':
            pokemessage = 'chevre'
        if pokemessage =='lewis' & (self.villager_store[0].lower() == 'jack'):
            pokemessage = 'jack'
            self.guarantee_shiny = True
        if self.villager_store is None:
            return False
        if self.villager_store[0].lower() == pokemessage:
            tempstore = self.villager_store
            self.villager_store = None

            shinyNum = random.randint(1, 1024)
            # sub
            if "692903238462341240" in [y.id for y in message.author.roles]:
                shinyNum = random.randint(1, 512)
            # tier 2
            if "692903238462341241" in [y.id for y in message.author.roles]:
                shinyNum = random.randint(1, 256)
            # boosters
            if "658383287600939059" in [y.id for y in message.author.roles]:
                shinyNum = random.randint(1, 256)
            # tier 3
            if "692903238462341242" in [y.id for y in message.author.roles]:
                shinyNum = random.randint(1, 128)

            # test switch

            response = requests.get("{}/shiny/{}.png".format(self.baseurl, tempstore[0]))
            if (response.status_code > 400):
                shinyNum = 2
            else:
                if (self.guarantee_shiny):
                    shinyNum = 1
                    self.guarantee_shiny = False

            embed = discord.Embed(type="rich", title="Gotcha!", color=0xEEE8AA)
            if shinyNum == 1:
                embed.description = ":sparkles: [{}]({}) :sparkles: was found by {}".format(tempstore[0].upper(),
                                                                                            "https://animalcrossing.fandom.com/wiki/{}".format(
                                                                                                tempstore[0]),
                                                                                            message.author.mention)
                embed.set_thumbnail(url="{}/shiny/{}.png".format(self.baseurl, tempstore[0]))
            else:
                embed.description = "[{}]({}) was found by {}".format(tempstore[0].upper(),
                                                                      "https://animalcrossing.fandom.com/wiki/{}".format(
                                                                          tempstore[0]), message.author.mention)
                embed.set_thumbnail(url="{}/normal/{}.png".format(self.baseurl, tempstore[0]))
            # await client.send_message(message.channel, "Gotcha!\n{} was caught by {}".format(self.pokestore['name'].upper(), message.author.mention))
            await message.channel.send(embed=embed)
            cursor = self.db.cursor()

            cursor.execute(f"SELECT captures.number from users "
                           f"INNER JOIN captures ON users.id = captures.user_id "
                           f"WHERE users.discord_id = {message.author.id} AND captures.villager_id = {tempstore[1]};")
            result = cursor.fetchone()
            if result is not None:
                cursor.execute(f"SELECT * FROM users WHERE discord_id = {message.author.id};")
                result = cursor.fetchone();
                id = result[0]
                if shinyNum == 1:
                    query = (
                        f"UPDATE captures "
                        "SET shiny_number = shiny_number + 1 "
                        f"WHERE user_id = {id} AND villager_id = {tempstore[1]};")
                else:
                    query = (
                        f"UPDATE captures "
                        "SET number = number + 1 "
                        f"WHERE user_id = {id} AND villager_id = {tempstore[1]};")
                cursor.execute(query)
            else:
                cursor.execute(f"SELECT id FROM users WHERE discord_id = {message.author.id};")
                result = cursor.fetchone();
                if result is None:
                    cursor.execute(f"INSERT INTO users (discord_id) VALUES ({message.author.id});")
                    cursor.execute(f"SELECT * FROM users WHERE discord_id = {message.author.id};")
                    result = cursor.fetchone();
                    id = result[0]
                else:
                    id = result[0]
                query = (
                    "INSERT INTO captures (user_id , villager_id, number) "
                    "VALUES (%s,%s, %s);"
                )
                values = (id, tempstore[1], 1)
                cursor.execute(query, values)
            self.db.commit()
            tempstore = None

            # if message.author.id in self.user_list.keys():
            #    self.user_list[message.author.id].generateHTML(message.author)
            self.time_to_spawn = datetime.now() + timedelta(seconds=random.randint(self.spawn_min, self.spawn_max))
            # await message.channel.send('Pokemon set to spawn!')
            await asyncio.sleep(self.getSeconds())
            await self._spawn(message)
            return True
        return False

    @commands.command(name='setrate')
    @commands.check(helper_perms)
    async def cmd_setrate(self, context, arg, arg1):
        self.spawn_min = int(arg)
        self.spawn_max = int(arg1)
        await context.channel.send("Spawnrate has been set to {}-{}seconds.".format(arg, arg1))

    @commands.command(name='getrate')
    @commands.is_owner()
    async def cmd_getrate(self, context):
        await context.channel.send("Spawnrate is {}-{}seconds.".format(self.spawn_min, self.spawn_max))

    @commands.command(name='clean')
    @commands.is_owner()
    async def cmd_clean(self, context, numMessages: int = 0):
        if numMessages == 0:
            for msg in self.bot.cached_messages:
                await msg.delete()
        else:
            deleted = await context.channel.purge(limit=numMessages + 1)

    @commands.command(name='shiny')
    @commands.check(admin_perms)
    async def cmd_shiny(self, context):
        self.guarantee_shiny = True

    @commands.command(name='ban')
    @commands.is_owner()
    async def cmd_ban(self, context, message):
        await context.channel.send("{} has been banned from CrossingCord.".format(message))
