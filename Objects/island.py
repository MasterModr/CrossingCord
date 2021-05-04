from Config import *
from Objects.PokeObj import *


class Island:
    def __init__(self, user, poke, oldIsland=None):
        if oldIsland is None:
            self.user = user.id
            self.pokeList = {poke[0]: [PokeObj(poke, user)]}
        else:
            self.user = oldIsland.user
            self.pokeList = oldIsland.pokeList
        self.backgroundImage = None

    def __repr__(self):
        prnt_str = "__{}'s Pokemon__: include **{}/802** Pokemon:\n".format(self.user.name, len(self.pokeList.keys()))
        for PokeName in self.pokeList.keys():
            prnt_str += "{} *x{}*\n".format(PokeName.capitalize(), len(self.pokeList[PokeName]))
        return prnt_str

    def getPokeList(self):
        values = []
        for key in self.pokeList.keys():
            values.append(int(self.pokeList[key][0].getindex()))
        return values

    def addPokeList(self, value, user):
        # print(value)
        if len(self.pokeList.keys()) > 9:
            return False
        if value[0] in self.pokeList.keys():
            return False
        else:
            self.pokeList[value[0]] = [PokeObj(value, user)]
            return True

    def removePokemon(self, name):
        if name in self.pokeList.keys():
            poke = self.pokeList[name].pop()
            if len(self.pokeList[name]) == 0:
                del self.pokeList[name]
            return poke
        else:
            return None

    def hasPokemon(self, name):
        if name in self.pokeList.keys():
            return True
        else:
            return False

    def listInventory(self):
        pass

    def hasBackground(self):
        if self.backgroundImage is None:
            return False
        else:
            return True

    def setBackground(self, background):
        self.backgroundImage = background

    def getBackground(self):
        return self.backgroundImage
