from datetime import datetime

class PokeObj:
    def __init__(self, pokeObj, psn):
        #print(pokeObj.keys())
        self.name = pokeObj[0]
        self.index = pokeObj[1]

        self.caughtBy = (datetime.now().strftime("%a, %b %d, %Y - %I:%M %p"), psn.id)

    def __repr__(self):
        return "{}#{}".format(self.name,self.index)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, PokeName):
        self._name = PokeName

    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, index):
        self._index = index
        
    def getindex(self):
        return self.index

    

