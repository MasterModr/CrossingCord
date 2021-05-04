from discord.ext import commands


class Commands(commands.Cog):
    def __init__(self, client):
        self.client = client



    @commands.command(name='newinventory')
    @commands.is_owner()
    async def cmd_newinventory(self, context):
        # prnt_txt = self.users_list[message.author]
        if context.author.id in self.users_list.keys():
            # print(self.users_list[context.author.id])
            self.users_list[context.author.id].generatenewHTML(context.author)
        else:
            msg = "{} you have no Villagers".format(context.author.name)
            await context.channel.send(msg)

    @commands.command(name='crimmas')
    @commands.is_owner()
    async def cmd_crimmas(self, context):
        # prnt_txt = self.users_list[message.author]
        id = context.author.id
        f = open("jingle.txt", "r+")
        contents = f.read()
        if "{}".format(id) in contents:
            msg = "You have already claimed your present."
            await context.channel.send(msg)
        else:
            contents = contents + "{}\n".format(id)
            f.seek(0)
            f.write(contents)
            f.truncate()
            embed = discord.Embed(type="rich", title="Merry Crimmas!!", color=0xEEE8AA)
            embed.description = ":sparkles: [{}]({}) :sparkles: was found by {}".format("Jingle",
                                                                                        "https://animalcrossing.fandom.com/wiki/Jingle",
                                                                                        context.author.mention)
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/715648683072421968/791718923993219122/jingleshiny.png")
            await context.channel.send(embed=embed)

    @commands.command(name='give')
    @commands.is_owner()
    async def cmd_give(self, context, arg, arg1):
        tempid = int(arg)
        tempid1 = int(arg1)
        tempstore = self.villagerdata[tempid1]
        obj = FakeUser(tempid)
        if tempid in self.users_list.keys():
            self.users_list[tempid].addPokeList(tempstore, obj)

        # NEVER RUN THIS EVER
        @commands.command(name='rebuild')
        @commands.is_owner()
        async def cmd_rebuild(self, context):
            directory = './www/'
            for filename in os.listdir(directory):
                if filename.endswith(".html"):
                    print(filename)
                    myid = int(filename.replace(".html", ""))
                    print(myid)
                    with open(directory + filename, "r") as myfile:
                        mytxt = myfile.read()
                        start_index = mytxt.find("""<h3 style="" class="text-center">""")
                        begin_index = start_index + len("""<h3 style="" class="text-center">""")
                        cuttxt = mytxt[begin_index:]
                        end_index = cuttxt.find("""<br><br><br>Obtained""") + begin_index
                        villagertxt = mytxt[begin_index:end_index]
                        buildvillagers = villagertxt.split('<br>')
                        counter = 0
                        for el in buildvillagers:
                            buildvillagers[counter] = el.split(' x')
                            counter += 1
                        print(buildvillagers)
                        persona = FakeUser(myid)
                        for el in buildvillagers:
                            counter = 0
                            idx = 0
                            for mylist in self.villagerdata:
                                if el[0].title() == mylist[0]:
                                    idx = int(mylist[1])
                            tempstore = self.villagerdata[idx]
                            while counter < int(el[1]):
                                if myid in self.users_list.keys():
                                    self.users_list[myid].addPokeList(tempstore, persona)
                                    print('yes')
                                else:
                                    self.users_list[myid] = User(persona, tempstore)
                                    print('no')
                                counter += 1
                                self.update_pickle()

def setup(client):
    client.add_cog(Commands(client))
