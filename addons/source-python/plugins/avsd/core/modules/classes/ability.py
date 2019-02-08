class Ability(object):
    name = None

    def __init__(self, index):
        self._index = index

    def activate(self, avsdplayer, skill, player, now):
        pass

    def get_cooldown(self, avsdplayer):
        return avsdplayer.data[self.name].get('cooldown', 0)

    def set_cooldown(self, avsdplayer, value):
        avsdplayer.data[self.name]['cooldown'] = value
