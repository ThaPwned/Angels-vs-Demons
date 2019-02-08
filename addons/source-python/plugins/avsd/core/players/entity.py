# ../avsd/core/players/entity.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Collections
from collections import defaultdict
#   Itertools
from itertools import chain
#   Random
from random import choice
#   Time
from time import time

# Source.Python Imports
#   Colors
from colors import BLACK
from colors import WHITE
from colors import YELLOW
from colors import ORANGE
from colors import RED
from colors import DARK_RED
from colors import GREEN
from colors import DARK_GREEN
#   Engines
from engines.server import global_vars
#   Entities
from entities import TakeDamageInfo
from entities.constants import DamageTypes
from entities.entity import Entity
from entities.helpers import index_from_pointer
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
#   Events
from events import Event
#   Filters
# from filters.players import PlayerIter
#   Listeners
from listeners import OnClientActive
from listeners import OnClientDisconnect
from listeners import OnEntityDeleted
from listeners.tick import Delay
#   Memory
from memory import make_object
from memory.manager import TypeManager
#   Messages
from messages import HintText
#   Players
from players.dictionary import PlayerDictionary
from players.helpers import get_client_language
from players.helpers import index_from_uniqueid
from players.helpers import index_from_userid
from players.helpers import uniqueid_from_playerinfo
from players.helpers import userid_from_index
from players.helpers import playerinfo_from_index

# AvsD Imports
#   Config
from ..config import experiences_data
# from ..config import items_data
#   Constants
from ..constants import CRYSTAL_CHAR
from ..constants import ItemQuality
from ..constants import MailStatus
from ..constants import QuestSort
from ..constants.paths import DATA_PATH
#   Database
from ..database.manager import database_manager
from ..database.manager import statements
#   Helpers
from ..helpers.particle import Particle
#   Items
from ..items import item_manager
#   Listeners
from ..listeners import OnPlayerAbilityPre
from ..listeners import OnPlayerAscend
from ..listeners import OnPlayerAscendPost
from ..listeners import OnPlayerDelete
from ..listeners import OnPlayerDestroy
from ..listeners import OnPlayerMailReceived
from ..listeners import OnPlayerReady
from ..listeners import OnPlayerStatsUpdatePre
from ..listeners import OnPlayerSwitchClass
from ..listeners import OnPlayerSwitchClassPost
from ..listeners import OnPlayerUIBuffPre
from ..listeners import OnPlayerUICooldownPre
from ..listeners import OnPlayerUIDebuffPre
from ..listeners import OnPlayerUIInfoPre
from ..listeners import OnPlayerUpgradeSkill
from ..listeners import OnTakeDamage
from ..listeners import OnTraceAttack
#   Modules
from ..modules.classes.manager import class_manager
#   Quests
from ..quests import quest_manager
#   Translations
from ..translations import ui_strings
from ..translations.strings import TranslationStrings


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
MAX_ASCENSIONS = max([int(x) for x in experiences_data['ascend']])
MAX_LEVEL = max([int(x) for x in experiences_data['required']]) + 1

manager = TypeManager()
CBaseEntity = manager.create_type_from_file('CBaseEntity', DATA_PATH / 'memory' / 'csgo' / 'CBaseEntity.ini')

_players = PlayerDictionary()

_global_weapon_entity = None
_global_bypass = False
_allow_abilities = True
_delays = defaultdict(set)

_general_level = Particle('_General_Level', lifetime=5)


# ============================================================================
# >> CLASSES
# ============================================================================
class _PlayerMeta(type):
    def __new__(mcs, name, bases, odict):
        cls = super().__new__(mcs, name, bases, odict)
        cls._players = {}
        cls._cache_userids = {}
        cls._cache_indexes = {}
        cls._cache_hud_info = {}

        return cls

    def __call__(cls, uniqueid):
        player = cls._players.get(uniqueid)

        if player is None:
            player = cls._players[uniqueid] = super().__call__(uniqueid)

        return player


class Player(object, metaclass=_PlayerMeta):
    def __init__(self, uniqueid):
        self._uniqueid = uniqueid
        self._classes = {}
        self._userid = None
        self._index = None
        self._player = None
        self._ready = False
        self._current_class = None
        self._is_bot = uniqueid.startswith('BOT_')
        self._state_manager = _StateManager(self)
        self._hud_info = None if self._is_bot else _HudInfo(self)
        self._inbox = None if self._is_bot else _Inbox(self)

        self._id = None
        self._name = None
        self._current_demon_class = None
        self._current_angel_class = None
        self._current_demon_vessel = None
        self._current_angel_vessel = None
        self._cash = None
        self._crystal = None
        self._quest_sort = None

        self.quests = {}
        # self.mails = {}

        self.data = defaultdict(dict)

        try:
            self._index = index_from_uniqueid(uniqueid)
        except ValueError:
            name = None
        else:
            self._userid = userid_from_index(self._index)

            Player._cache_userids[self.userid] = self
            Player._cache_indexes[self.index] = self

            name = playerinfo_from_index(self.index).name

        if not database_manager._unloading:
            database_manager.execute('player get', (uniqueid, ), callback=self._query_get_player, name=name)

    def _query_get_player(self, result):
        if database_manager._unloading:
            return

        data = result.fetchone()

        if data is None:
            database_manager.execute('player insert', (self.uniqueid, result['name'], class_manager.default_demon, class_manager.default_angel, 0, 0, 0, 0, 0))
            database_manager.execute('player get', (self.uniqueid, ), callback=self._query_get_player, name=result['name'])
            return

        self._id = data[0]
        self._name = data[1]
        self._current_demon_class = data[2]
        self._current_angel_class = data[3]
        self._current_demon_vessel = data[4]
        self._current_angel_vessel = data[5]
        self._cash = data[6]
        self._crystal = data[7]
        self._quest_sort = QuestSort(data[8])

        if self._current_demon_class not in class_manager:
            self._current_demon_class = class_manager.default_demon

        if self._current_angel_class not in class_manager:
            self._current_angel_class = class_manager.default_angel

        if result['name'] is not None:
            self._name = result['name']

        database_manager.execute('class get', (self.id, ), callback=self._query_get_classes)

    def _query_get_classes(self, result):
        if database_manager._unloading:
            return

        data = result.fetchall()

        if data:
            for name, xp, level, point, ascend, slot in data:
                if name in class_manager:
                    self._classes[name] = _Class(self, name, xp, level, point, ascend, slot)

        classes = []

        for name in class_manager:
            if name not in self._classes:
                classes.append((name, self.id, 0, 1, 1, 0, 5))

                self._classes[name] = _Class(self, name, 0, 1, 1, 0, 5)

        if classes:
            database_manager.executemany('class insert', classes)

        database_manager.execute('skill get', (self.id, ), callback=self._query_get_skills)

    def _query_get_skills(self, result):
        if database_manager._unloading:
            return

        data = result.fetchall()

        if data:
            for name, class_name, level in data:
                if class_name in self._classes:
                    class_ = self._classes[class_name]
                    class_.skills[name] = _Skill(self, class_, name, level)

        skills = []

        for class_name in class_manager:
            class_ = self._classes[class_name]

            for name in class_.settings.config.get('skills', []):
                if name not in class_.skills:
                    skills.append((name, self.id, class_name, 0))

                    class_.skills[name] = _Skill(self, class_, name, 0)

            for name in class_.settings.config.get('passives', []):
                # if name not in class_.passives:
                class_.passives[name] = _Passive(self, class_, name)

        if skills:
            database_manager.executemany('skill insert', skills)

        database_manager.execute('item get', (self.id, ), callback=self._query_get_items)

    def _query_get_items(self, result):
        if database_manager._unloading:
            return

        data = result.fetchall()

        if data:
            # for name, class_name, fakeid, quality, equipped, count in data:
            for name, class_name, quality, equipped, count in data:
                if class_name in self._classes:
                    # if count is None:
                    #     print('found None - preventing item adding')
                    #     continue

                    class_ = self._classes[class_name]
                    # class_.items.append(_Item(self, class_, name, fakeid, ItemQuality(quality), bool(equipped)))
                    class_.items.append(_Item(class_, name, ItemQuality(quality), bool(equipped), count=count))

        if self._is_bot:
            self._query_final()
        else:
            database_manager.execute('quest get', (self.id, ), callback=self._query_get_quests)

    def _query_get_quests(self, result):
        if database_manager._unloading:
            return

        data = result.fetchall()

        if data:
            for quest_name, completed, rewarded in data:
                self.quests[quest_name] = {'completed':completed, 'rewarded':rewarded, 'requirements':{}}

        quests = []

        for quest_name in quest_manager:
            if quest_name not in self.quests:
                quests.append((quest_name, self.id, 0, 0))

                self.quests[quest_name] = {'completed':0, 'rewarded':0, 'requirements':{}}

        if quests:
            database_manager.executemany('quest insert', quests)

        database_manager.execute('requirement get', (self.id, ), callback=self._query_get_requirements)

    def _query_get_requirements(self, result):
        if database_manager._unloading:
            return

        data = result.fetchall()

        if data:
            for quest_name, require_name, progress in data:
                self.quests[quest_name]['requirements'][require_name] = progress

        requirements = []

        for quest_name, quest in quest_manager.items():
            for requirement in quest.requirements:
                if requirement.name not in self.quests[quest_name]['requirements']:
                    requirements.append((quest_name, self.id, requirement.name, 0))

                    self.quests[quest_name]['requirements'][requirement.name] = 0

        if requirements:
            database_manager.executemany('requirement insert', requirements)

        database_manager.execute('mail get', (self.id, ), callback=self._query_get_mails)

    def _query_get_mails(self, result):
        if database_manager._unloading:
            return

        data = result.fetchall()

        if data:
            # for id_, source, name, message, status in data:
            for id_, source, message, status in data:
                # self.inbox.append(_Mail(id_, source, message, MailStatus(status), []))
                self.inbox.append({'id':id_, 'source':source, 'message':message, 'status':MailStatus(status), 'rewards':[]})

        database_manager.execute('mail reward get', (self.id, ), callback=self._query_get_mail_rewards)

    def _query_get_mail_rewards(self, result):
        if database_manager._unloading:
            return

        data = result.fetchall()

        if data:
            for mail in self.inbox:
                for mailid, name, value in data:
                    # if mail.id == mailid:
                    if mail['id'] == mailid:
                        # mail.rewards.append({'name':name, 'value':value})
                        mail['rewards'].append({'name':name, 'value':value})

        # database_manager.callback(self._query_final)
        self._query_final()

    # def _query_final(self, result):
    def _query_final(self):
        if database_manager._unloading:
            return

        self._ready = True

        try:
            # We need to make sure the uniqueid (the player) is in the server
            index_from_uniqueid(self.uniqueid)
        except ValueError:
            pass
        else:
            current_class = {2:self._current_demon_class, 3:self._current_angel_class}.get(self.player.team_index)

            if current_class is not None:
                OnPlayerSwitchClass.manager.notify(self, None, current_class)

            self._current_class = current_class

            for class_ in self._classes.values():
                class_.update_cache()

            OnPlayerReady.manager.notify(self)

            if current_class is not None:
                OnPlayerSwitchClassPost.manager.notify(self, None, current_class)

                self.update_clan_tag()

    def _query_save(self, result):
        # We don't want them to have previous data
        # This has to be done here, as it'll cause errors if it's done in OnClientDisconnect
        self.data.clear()

        try:
            self._index = index_from_uniqueid(self.uniqueid)
        except ValueError:
            OnPlayerDestroy.manager.notify(self)

            del Player._players[self.uniqueid]

            self._userid = None
            self._index = None
        else:
            self._userid = userid_from_index(self.index)

    def save(self):
        assert self.ready

        # TODO: This could use a hand...

        database_manager.execute('player update', (self.name, self._current_demon_class, self._current_angel_class, self._current_demon_vessel, self._current_angel_vessel, self._cash, self._crystal, self._quest_sort.value, self._id))

        join = statements['class join']

        xp = ' '.join([join % (name, class_.xp) for name, class_ in self._classes.items()])
        level = ' '.join([join % (name, class_.level) for name, class_ in self._classes.items()])
        point = ' '.join([join % (name, class_.point) for name, class_ in self._classes.items()])
        ascend = ' '.join([join % (name, class_.ascend) for name, class_ in self._classes.items()])
        slot = ' '.join([join % (name, class_.slot) for name, class_ in self._classes.items()])

        database_manager.execute_text(statements['class update'] % (xp, level, point, ascend, slot), (self._id, ))

        join = statements['skill join']

        level = ' '.join([join % (name, skill.level) for class_ in self._classes.values() for name, skill in class_.skills.items()])

        database_manager.execute_text(statements['skill update'] % (level, ), (self._id, ))

        items = list(chain.from_iterable([class_.items for class_ in self._classes.values()]))

        if items:
            join = statements['item join']

            # removeable = [item for item in items if item._remove]
            removeable = [item for item in items if not item.count]

            if removeable:
                # database_manager.execute_text(statements['item cleanup'] % ', '.join('?' for _ in removeable), [self._id] + [item.fakeid for item in removeable])
                for class_ in self._classes.values():
                    for item in list(class_.items):
                        # for removed_item in removeable:
                        if item in removeable:
                            # if item.fakeid == removed_item.fakeid:
                            class_.items.remove(item)
                            # break

                items = [item for item in items if item not in removeable]

            add = [item for item in items if not item._added]

            if add:
                # database_manager.executemany('item insert', [(item.name, self._id, item.class_.name, item.fakeid, item.quality.value, item.equipped, item.count) for item in add])
                database_manager.executemany('item insert', [(item.name, self._id, item.class_.name, item.quality.value, item.equipped, item.count) for item in add])

                for item in add:
                    item._added = True

                items = [item for item in items if item not in add]

            if items:
                # equipped = ' '.join([join % (item.name, item.fakeid, int(item.equipped)) for item in items])
                equipped = ' '.join([join % (item.name, item.class_.name, item.quality.value, int(item.equipped)) for item in items])
                count = ' '.join([join % (item.name, item.class_.name, item.quality.value, item.count) for item in items])

                # database_manager.execute_text(statements['item update'] % (equipped, ), (self._id, ))
                database_manager.execute_text(statements['item update'] % (equipped, count), (self._id, ))

        if self.quests:
            join = statements['quest join']

            completed = ' '.join([join % (name, quest['completed']) for name, quest in self.quests.items()])
            rewarded = ' '.join([join % (name, quest['rewarded']) for name, quest in self.quests.items()])

            database_manager.execute_text(statements['quest update'] % (completed, rewarded), (self._id, ))

            join = statements['requirement join']

            progress = ' '.join([join % (require_name, quest_name, progress) for quest_name, quest in self.quests.items() for require_name, progress in quest['requirements'].items()])

            database_manager.execute_text(statements['requirement update'] % (progress, ), (self._id, ))

        # if self.mails:
        if self.inbox:
            join = statements['mail join']

            removeable = [mail for mail in self.inbox if mail['status'] is MailStatus.DELETE]
            # removeable = [mail for mail in self.inbox if mail.status is MailStatus.DELETE]

            if removeable:
                database_manager.execute_text(statements['mail delete'] % ', '.join('?' * len(removeable)), [mail['id'] for mail in removeable])
                database_manager.execute_text(statements['mail reward delete'] % ', '.join('?' * len(removeable)), [mail['id'] for mail in removeable])

                for mail in removeable:
                    self.inbox.remove(mail)

            # add = [id_ for id_ in self.mails if not self.mails[id_]['added']]

            # if add:
            #     database_manager.executemany('mail insert', [(self._id, self.mails[id_]['source'], self.mails[id_]['name'], self.mails[id_]['message'], self.mails[id_]['status'].value) for id_ in add])
            #     database_manager.executemany('mail reward insert', [(self._id, self.mails[id_]['source'], self.mails[id_]['name'], self.mails[id_]['message'], self.mails[id_]['status'].value) for id_ in add])

            #     for id_ in add:
            #         self.mails[id_]['added'] = True

            if self.inbox:
                status = ' '.join([join % (mail['id'], mail['status'].value) for mail in self.inbox])
                # status = ' '.join([join % (mail.id, mail.status.value) for mail in self.inbox])

                database_manager.execute_text(statements['mail update'] % (status, ), (self._id, ))

        # self.mails[id_] = {'source':source, 'name':name, 'message':message, 'status':MailStatus(status), 'rewards':[], 'added':True}
        # self.mails[mailid]['rewards'].append({'id':id_, 'name':name, 'value':value})

    def take_damage(self, damage, attacker, class_, skill, skip_hooks=True):
        # TODO: This method should not have been called if the victim is already dead
        assert not self.player.dead

        if not self.player.dead:
            global _global_bypass

            _global_bypass = skip_hooks

            take_damage_info = TakeDamageInfo()
            take_damage_info.attacker = attacker

            global _global_weapon_entity

            if _global_weapon_entity is None:
                _global_weapon_entity = Entity.create('info_target')

            _global_weapon_entity.set_key_value_string('classname', f'avsd_{class_}_{skill}')

            take_damage_info.weapon = _global_weapon_entity.index
            take_damage_info.inflictor = _global_weapon_entity.index
            take_damage_info.damage = damage
            take_damage_info.type = DamageTypes.GENERIC

            try:
                self.player.on_take_damage(take_damage_info)
            finally:
                _global_bypass = False

    def take_delayed_damage(self, damage, attacker, class_, skill, skip_hooks=True):
        # TODO: This method should not have been called if the victim is already dead
        assert not self.player.dead

        attacker = userid_from_index(attacker)

        delay = Delay(0, self._take_delayed_damage, args=(damage, attacker, class_, skill, skip_hooks))
        delay.args += (delay, )

        _delays[self.userid].add(delay)

    def _take_delayed_damage(self, damage, attacker, class_, skill, skip_hooks, delay):
        _delays[self.userid].discard(delay)

        assert not self.player.dead

        try:
            attacker = index_from_userid(attacker)
        except ValueError:
            attacker = 0

        self.take_damage(damage, attacker, class_, skill, skip_hooks)

    def update_clan_tag(self):
        self.player.clan_tag = f'[{self.current_class.capitalize()}: L{self.level}]: '

    @property
    def userid(self):
        assert self._userid is not None

        return self._userid

    @property
    def index(self):
        assert self._index is not None

        return self._index

    @property
    def uniqueid(self):
        return self._uniqueid

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, value):
        self._cash = value

    @property
    def crystal(self):
        return self._crystal

    @crystal.setter
    def crystal(self, value):
        self._crystal = value

    @property
    def ready(self):
        return self._ready

    @property
    def player(self):
        if self._player is None:
            self._player = _players[self.index]

        return self._player

    @property
    def current_class(self):
        return self._current_class

    @current_class.setter
    def current_class(self, value):
        assert value in self.allowed_classes

        old = self._current_class

        assert old != value

        OnPlayerSwitchClass.manager.notify(self, old, value)

        self._current_class = value
        setattr(self, '_current_demon_class' if self.player.team_index == 2 else '_current_angel_class', value)

        OnPlayerSwitchClassPost.manager.notify(self, old, value)

        self.update_clan_tag()

    @property
    def active_class(self):
        return self._classes.get(self.current_class)

    @property
    def classes(self):
        return self._classes

    @property
    def passives(self):
        return self.active_class.passives

    @property
    def skills(self):
        return self.active_class.skills

    @property
    def items(self):
        return self.active_class.items

    @property
    def stats(self):
        return self.active_class.stats

    @property
    def xp(self):
        return self.active_class.xp

    @xp.setter
    def xp(self, value):
        self.active_class.xp = value

    @property
    def level(self):
        return self.active_class.level

    @level.setter
    def level(self, value):
        self.active_class.level = value

    @property
    def point(self):
        return self.active_class.point

    @point.setter
    def point(self, value):
        self.active_class.point = value

    @property
    def ascend(self):
        return self.active_class.ascend

    @ascend.setter
    def ascend(self, value):
        self.active_class.ascend = value

    @property
    def slot(self):
        return self.active_class.slot

    @slot.setter
    def slot(self, value):
        self.active_class.slot = value

    @property
    def max_slots(self):
        return self.active_class.max_slots

    @property
    def state(self):
        return self._state_manager

    @property
    def hudinfo(self):
        return self._hud_info

    @property
    def inbox(self):
        return self._inbox

    @property
    def allowed_classes(self):
        team = self.player.team_index

        assert team in (2, 3)

        class_type = 'demon' if team == 2 else 'angel'

        return [name for name, x in class_manager.items() if x.settings.config['class'] == class_type]

    @classmethod
    def from_index(cls, index):
        avsdplayer = cls._cache_indexes.get(index)

        if avsdplayer is None:
            playerinfo = playerinfo_from_index(index)
            uniqueid = uniqueid_from_playerinfo(playerinfo)

            avsdplayer = cls._cache_indexes[index] = cls(uniqueid)

        return avsdplayer

    @classmethod
    def from_userid(cls, userid):
        avsdplayer = cls._cache_userids.get(userid)

        if avsdplayer is None:
            index = index_from_userid(userid)
            playerinfo = playerinfo_from_index(index)
            uniqueid = uniqueid_from_playerinfo(playerinfo)

            avsdplayer = cls._cache_userids[userid] = cls(uniqueid)

        return avsdplayer


class _Class(object):
    def __init__(self, avsdplayer, name, xp, level, point, ascend, slot):
        self.avsdplayer = avsdplayer
        self.name = name
        self._xp = xp
        self._level = level
        self._point = point
        self._ascend = ascend
        self._slot = slot
        self._total_xp = None

        self.settings = class_manager[self.name].settings

        self.passives = {}
        self.skills = {}
        # self.items = _ItemContainer(avsdplayer, self)
        self.items = _ItemContainer(self)
        self.stats = {}

    def _get_total_xp(self):
        if self._total_xp is None:
            required = experiences_data['required']

            # xp = sum([required[str(x)] for x in range(1, self.level)])
            self._total_xp = sum([required[str(x)] for x in range(1, self.level)])

            if self.ascend:
                # return round(xp * (experiences_data['ascend'][str(self.ascend)] + 1))
                self._total_xp = round(self._total_xp * (experiences_data['ascend'][str(self.ascend)] + 1))

        # return xp
        return self._total_xp

    def _get_required_xp(self, level=None):
        if level is None:
            level = self.level

        if self.ascend:
            return round(experiences_data['required'][str(level)] * (experiences_data['ascend'][str(self.ascend)] + 1))

        return experiences_data['required'][str(level)]

    def _upgrade_skills(self):
        skills = [x for x in self.skills.values() if x.enabled and x.level < x.max]

        if skills:
            levels = defaultdict(int)

            for i in range(self.point):
                self.point -= 1

                skill = choice(skills)

                levels[skill] += 1

                if skill.level + levels[skill] == skill.max:
                    skills.remove(skill)

                    if not skills:
                        break

            for skill, level in levels.items():
                OnPlayerUpgradeSkill.manager.notify(self.avsdplayer, skill, skill.level, skill.level + level)

                skill.level += level

    def update_cache(self, from_level=None):
        config = self.settings.config

        if from_level is None:
            data = config['default']['ascend{0}'.format(self.ascend)]

            for name, value in data.items():
                self.stats[name] = value

            for item in self.items.valid:
                if item.equipped:
                    item._cache()

        stats = defaultdict(int)

        for level, unlocks in config['unlocks'].items():
            level = int(level)

            if level > self.level:
                break

            if from_level is not None and level <= from_level:
                continue

            if isinstance(unlocks, str):
                unlocks = [unlocks]

            for data in unlocks:
                # This is temporary
                try:
                    if data.startswith('unlock'):
                        self.skills[data.split(':')[1]].enabled = True
                    elif data.startswith(('passive', 'skill')):
                        type_, skill, name, value = data.split(':')

                        getattr(self, type_ + 's')[skill].stats[name] += (float if '.' in value else int)(value)
                    else:
                        name, value = data.split(':')

                        stats[name] += (float if '.' in value else int)(value)
                except:
                    from hooks.exceptions import except_hooks

                    except_hooks.print_exception()

        OnPlayerStatsUpdatePre.manager.notify(self.avsdplayer, self, from_level is None, stats)

        for name, value in stats.items():
            self.stats[name] += value

    @property
    def xp(self):
        return self._xp

    @xp.setter
    def xp(self, value):
        new_level = self.level

        if new_level == MAX_LEVEL:
            return

        required_xp = self._get_required_xp(new_level)

        while value >= required_xp:
            value -= required_xp

            new_level += 1

            if new_level == MAX_LEVEL:
                value = 0
                break

            required_xp = self._get_required_xp(new_level)

        self._xp = value
        self._total_xp = None

        if new_level != self.level:
            self.level = new_level

    @property
    def total_xp(self):
        return self._get_total_xp() + self.xp

    @property
    def total_required_xp(self):
        if self.level == MAX_LEVEL:
            return self._get_total_xp()

        return self._get_total_xp() + self._get_required_xp(self.level)

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        assert value <= MAX_LEVEL
        assert self.level != MAX_LEVEL

        if value == MAX_LEVEL:
            if self.avsdplayer._is_bot:
                if self.ascend < MAX_ASCENSIONS:
                    self.ascend += 1

                    return

        from_level = self.level

        self.point += value - from_level

        self._level = value

        if self.avsdplayer._is_bot:
            self._upgrade_skills()

        if self.avsdplayer._current_class == self.name:
            player = self.avsdplayer.player

            if not player.dead:
                _general_level.create(player.origin)

        self.update_cache(from_level)

        self.avsdplayer.update_clan_tag()

    @property
    def point(self):
        return self._point

    @point.setter
    def point(self, value):
        self._point = value

    @property
    def ascend(self):
        return self._ascend

    @ascend.setter
    def ascend(self, value):
        OnPlayerAscend.manager.notify(self.avsdplayer, self)

        self._xp = 0
        self._level = 1
        self._point = 1
        self._ascend = value
        self._total_xp = None

        self.avsdplayer.update_clan_tag()

        self.stats.clear()

        for skill in self.skills.values():
            skill.level = 0
            skill.stats.clear()

        self.update_cache()

        OnPlayerAscendPost.manager.notify(self.avsdplayer, self)

        if self.avsdplayer._is_bot:
            self._upgrade_skills()

    @property
    def slot(self):
        return self._slot

    @slot.setter
    def slot(self, value):
        self._slot = value

    @property
    def max_slots(self):
        # inventory = items_data['inventory']

        # return inventory['default'] + inventory['increase'] * self.slot
        return item_manager.get_max_slots(self.slot)

    @property
    def abilities(self):
        return self.settings._abilities


class _BaseSkill(object):
    def __init__(self, avsdplayer, class_, name, type_):
        self.avsdplayer = avsdplayer
        self.class_ = class_
        self.name = name
        self.stats = defaultdict(int)

        self._settings = self.class_.settings
        self._config = self._settings.config[type_][self.name]

    def __getitem__(self, name):
        return self._config[name] + self.stats.get(name, 0)


class _Passive(_BaseSkill):
    def __init__(self, avsdplayer, class_, name):
        super().__init__(avsdplayer, class_, name, 'passives')


class _Skill(_BaseSkill):
    def __init__(self, avsdplayer, class_, name, level):
        super().__init__(avsdplayer, class_, name, 'skills')

        # self.level = level
        self.level = self._config['max']
        self.enabled = True
        self.max = self._config['max']

        self._ability = self._settings._abilities.get(name)

    def __call__(self):
        if _allow_abilities:
            player = self.avsdplayer.player

            assert not player.dead

            if self.enabled and self.level:
                now = time()

                if self.cooldown <= now:
                    data = {'allow':True}

                    OnPlayerAbilityPre.manager.notify(self.avsdplayer, data)

                    if data['allow']:
                        self._ability.activate(self.avsdplayer, self, player, now)

    @property
    def cooldown(self):
        return self._ability.get_cooldown(self.avsdplayer)

    @cooldown.setter
    def cooldown(self, value):
        self._ability.set_cooldown(self.avsdplayer, value)


class _ItemContainer(list):
    # def __init__(self, avsdplayer, class_):
    def __init__(self, class_):
        super().__init__()

        # self.avsdplayer = avsdplayer
        self.class_ = class_

    def give(self, name, quality):
        for item in self:
            if item.name == name and item.quality == quality:
                item.count += 1
                # item._remove = False
                break
        else:
            # fakeid = max([item.fakeid for item in chain.from_iterable([class_.items for class_ in self.avsdplayer._classes.values()]) if not item._remove], default=-1) + 1
            # fakeid = max([item.fakeid for item in self if not item._remove], default=-1) + 1

            # item = _Item(self.avsdplayer, self.class_, name, fakeid, quality, False, False)
            # item = _Item(self.class_, name, fakeid, quality, False, False)
            item = _Item(self.class_, name, quality, False, added=False)
            self.append(item)

    @staticmethod
    def destroy(item):
        assert item.count > 0

        item.count -= 1

        # if not item.count:
        #     if item._added:
        #         item._remove = True
        #     else:
        #         self.remove(item)

    @property
    def valid(self):
        # return [item for item in self if not item._remove]
        return [item for item in self if item.count]

    @property
    def total(self):
        return sum([item.count for item in self.valid])

    @property
    def total_unequipped(self):
        return sum([item.count if not item.equipped else item.count - 1 for item in self.valid])


class _Item(object):
    # def __init__(self, avsdplayer, class_, name, fakeid, quality, equipped, added=True):
    # def __init__(self, class_, name, fakeid, quality, equipped, added=True, count=0):
    def __init__(self, class_, name, quality, equipped, count=1, added=True):
        assert isinstance(quality, ItemQuality)

        # self._avsdplayer = avsdplayer
        self.class_ = class_
        self.name = name
        # self.fakeid = fakeid
        self.quality = quality
        self._equipped = equipped
        self.count = count
        # self._config = items_data['items'][name]
        self._config = item_manager[name]
        self._added = added
        # self._remove = False

        unlocks = self._config['quality'][self.quality.name.lower()]

        if isinstance(unlocks, str):
            unlocks = [unlocks]

        self._unlocks = unlocks

    def _cache(self, positive=True):
        for data in self._unlocks:
            # This is temporary
            try:
                if data.startswith(('passive', 'skill')):
                    type_, skill, name, value = data.split(':')

                    getattr(self.class_, type_ + 's')[skill].stats[name] += (float if '.' in value else int)(value if positive else value * -1)
                else:
                    name, value = data.split(':')

                    self.class_.stats[name] += (float if '.' in value else int)(value if positive else value * -1)
            except:
                from hooks.exceptions import except_hooks

                except_hooks.print_exception()

    @property
    def equipped(self):
        return self._equipped

    @equipped.setter
    def equipped(self, value):
        assert isinstance(value, bool)
        assert value != self._equipped

        self._equipped = value

        self._cache(value)


class _StateManager(defaultdict):
    def __init__(self, avsdplayer):
        super().__init__(int)

        self._avsdplayer = avsdplayer

    def __setitem__(self, item, value):
        assert value >= 0

        if item not in self:
            super().__setitem__(item, value)

        player = self._avsdplayer.player

        if not player.dead:
            if value and not self[item]:
                setattr(player, item, True)
            elif not value and self[item]:
                setattr(player, item, False)

        super().__setitem__(item, value)


class _HudInfo(object):
    def __init__(self, avsdplayer):
        self._avsdplayer = avsdplayer
        self._entity = None
        self._messages = []

    def show(self):
        avsdplayer = self._avsdplayer
        player = avsdplayer.player
        active_class = avsdplayer.active_class
        language = get_client_language(avsdplayer.index)

        # Create the game_text if it does not exist
        if self._entity is None:
            entity = self._entity = Entity.create('game_text')
            entity.set_key_value_int('effect', 0)
            entity.set_key_value_float('scantime', 0)
            entity.set_key_value_float('fadein', 0)
            entity.set_key_value_float('fadeout', 0)
            entity.set_key_value_float('fxtime', 0)
            entity.set_key_value_float('holdtime', 0.5)
            entity.set_key_value_int('spawnflags', 0)
            entity.spawn()

            Player._cache_hud_info[entity.inthandle] = avsdplayer

        now = time()

        # Current class, level, xp/required xp, cash, and crystal
        self._entity.set_key_value_int('channel', 1)
        self._entity.set_key_value_color('color', WHITE)
        self._entity.set_key_value_color('color2', BLACK)
        self._entity.set_key_value_float('x', -1)
        self._entity.set_key_value_float('y', 0.1)

        if avsdplayer.crystal:
            text = ui_strings['ui info crystal']
            text = text.get_string(language, name=active_class.settings.strings['name'], level=active_class.level, total_xp=active_class.total_xp, total_required_xp=active_class.total_required_xp, cash=avsdplayer.cash, crystal_char=CRYSTAL_CHAR, crystal=avsdplayer.crystal)
        else:
            text = ui_strings['ui info']
            text = text.get_string(language, name=active_class.settings.strings['name'], level=active_class.level, total_xp=active_class.total_xp, total_required_xp=active_class.total_required_xp, cash=avsdplayer.cash)

        # Information
        messages = []

        OnPlayerUIInfoPre.manager.notify(avsdplayer, active_class, language, messages, now)

        if messages:
            text += '\n' * 13 + '\n'.join(messages)

        self._entity.set_key_value_string('message', text)

        self._entity.call_input('Display', activator=player)

        # XP gained
        if self._messages:
            self._entity.set_key_value_int('channel', 2)
            self._entity.set_key_value_color('color', ORANGE)
            self._entity.set_key_value_color('color2', YELLOW)
            self._entity.set_key_value_float('y', 0.2)

            messages = []

            for info in self._messages.copy():
                if info['life'] >= now:
                    messages.append(info['message'])
                else:
                    if 'fadeout' not in info:
                        info['fadeout'] = now + 0.3

                    if info['fadeout'] >= now:
                        messages.append(' ')
                    else:
                        self._messages.remove(info)

            if messages:
                self._entity.set_key_value_string('message', '\n'.join(messages))

                self._entity.call_input('Display', activator=player)

        # Buffs
        messages = []

        OnPlayerUIBuffPre.manager.notify(avsdplayer, active_class, language, messages, now)

        if messages:
            self._entity.set_key_value_int('channel', 3)
            self._entity.set_key_value_color('color', GREEN)
            self._entity.set_key_value_color('color2', DARK_GREEN)
            self._entity.set_key_value_float('x', 0)
            self._entity.set_key_value_float('y', 0.75)
            self._entity.set_key_value_string('message', '\n'.join(messages))
            self._entity.call_input('Display', activator=player)

        # Debuffs
        messages = []

        OnPlayerUIDebuffPre.manager.notify(avsdplayer, active_class, language, messages, now)

        if messages:
            self._entity.set_key_value_int('channel', 4)
            self._entity.set_key_value_color('color', RED)
            self._entity.set_key_value_color('color2', DARK_RED)
            self._entity.set_key_value_float('x', 0.3)
            self._entity.set_key_value_float('y', 0.75)
            self._entity.set_key_value_string('message', '\n'.join(messages))
            self._entity.call_input('Display', activator=player)

        # Hinttext
        messages = []

        OnPlayerUICooldownPre.manager.notify(avsdplayer, active_class, language, messages, now)

        if messages:
            if len(messages) > 3:
                chunk = int(round(len(messages) / 3))

                assert chunk, 'Should not happen'

                result = [messages[i:i + chunk] for i in range(0, len(messages), chunk)]

                if len(result) == 4:
                    extra = result.pop(3)
                    result[2].append(extra[0])

                if len(result) == 3:
                    if len(result[2]) > len(result[0]):
                        value = result[2].pop(0)
                        result[1].append(value)
                        value = result[1].pop(0)
                        result[0].append(value)

                messages = [' | '.join(x) for x in result]

            HintText('\n'.join(messages)).send(avsdplayer.index)

    def add_message(self, message, **tokens):
        if isinstance(message, TranslationStrings):
            message = message.get_string(get_client_language(self.avsdplayer.index), **tokens)

        self._messages.append({'life':time() + 3, 'message':message})


class _Inbox(list):
    def __init__(self, avsdplayer):
        super().__init__()

        self._avsdplayer = avsdplayer

    def receive(self, message, source=None, rewards=None):
        database_manager.execute('mail insert', (self._avsdplayer.id, source, message, MailStatus.NEW), callback=self._add_mail_rewards, source=source, message=message, rewards=rewards)

    def _add_mail_rewards(self, result):
        mailid = result.lastrowid

        if result['rewards']:
            rewards = []

            playerid = self._avsdplayer.id

            for name, value in result['rewards'].items():
                rewards.append((mailid, playerid, name, value))

            database_manager.executemany('mail reward insert', rewards, callback=self._received_mail, id=mailid, source=result['source'], message=result['message'], rewards=result['rewards'])
        else:
            self._received_mail({'id':mailid, 'source':result['source'], 'message':result['message'], 'rewards':result['rewards']})

    def _received_mail(self, result):
        mail = {'id':result['id'], 'source':result['source'], 'message':result['message'], 'status':MailStatus.NEW, 'rewards':[]}
        # mail = _Mail(result['id'], result['source'], result['message'], MailStatus.NEW, [])

        for name, value in result['rewards'].items():
            mail['rewards'].append({'name':name, 'value':value})
            # mail.rewards.append({'name':name, 'value':value})

        self.append(mail)

        self._avsdplayer.hudinfo.add_message('You received mail!')

        OnPlayerMailReceived.manager.notify(self._avsdplayer, mail)

    @property
    def valid(self):
        return [mail for mail in self if mail['status'] is not MailStatus.DELETE]
        # return [mail for mail in self if mail.status is not MailStatus.DELETE]


# ============================================================================
# >> LISTENERS
# ============================================================================
@OnClientActive
def on_client_active(index):
    avsdplayer = Player(uniqueid_from_playerinfo(playerinfo_from_index(index)))

    avsdplayer._userid = userid_from_index(index)
    avsdplayer._index = index


@OnClientDisconnect
def on_client_disconnect(index):
    # This can occur if the player leaves the server before OnClientActive was called
    try:
        uniqueid = uniqueid_from_playerinfo(playerinfo_from_index(index))
    except ValueError:
        return

    avsdplayer = Player(uniqueid)

    # If we failed to get the correct uniqueid for some reason, do not proceed
    assert avsdplayer.uniqueid == uniqueid, (avsdplayer.uniqueid, uniqueid)

    OnPlayerDelete.manager.notify(avsdplayer)

    for delay in _delays[avsdplayer.userid]:
        delay.cancel()

    del _delays[avsdplayer.userid]

    del Player._cache_userids[avsdplayer.userid]
    del Player._cache_indexes[avsdplayer.index]

    if avsdplayer.ready:
        avsdplayer.save()

    # TODO: In testing phase to see if it's anything worth having
    from warnings import warn
    from listeners.tick import Repeat
    from listeners.tick import RepeatStatus

    def get_delays(data):
        for name, value in data.items():
            if isinstance(value, (Delay, Repeat)):
                yield value
            elif isinstance(value, dict):
                yield from get_delays(value)

    for instance in get_delays(avsdplayer.data):
        if isinstance(instance, Delay):
            if instance.running:
                # print('running delay found, stopping...')
                warn(f'Found delay {instance.callback} running ({instance.args} {instance.kwargs})), stopping...')
                instance.cancel()
        else:
            if instance.status == RepeatStatus.RUNNING:
                # print('running repeat found, stopping...')
                warn(f'Found repeat {instance.callback} running ({instance.args} {instance.kwargs})), stopping...')
                instance.stop()

    database_manager.callback(avsdplayer._query_save)


@OnEntityDeleted
def on_entity_deleted(base_entity):
    if not base_entity.is_networked():
        return

    avsdplayer = Player._cache_hud_info.pop(base_entity.inthandle, None)

    if avsdplayer is not None:
        avsdplayer.hudinfo._entity = None

    avsdplayer = Player._cache_indexes.pop(base_entity.index, None)

    if avsdplayer is not None:
        avsdplayer._player = None

    global _global_weapon_entity

    if _global_weapon_entity is not None:
        if base_entity.index == _global_weapon_entity.index:
            _global_weapon_entity = None


# for player in PlayerIter():
#     Player(player.uniqueid)


# ============================================================================
# >> HOOKS
# ============================================================================
@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def pre_on_take_damage(stack):
    if _global_bypass:
        return

    info = make_object(TakeDamageInfo, stack[1])
    attacker = info.attacker

    if attacker != info.inflictor:
        return

    index = index_from_pointer(stack[0])

    if 0 < attacker <= global_vars.max_clients:
        if index == attacker:
            return

        avsdvictim = Player.from_index(index)
        avsdattacker = Player.from_index(attacker)

        if avsdattacker.player.team_index == avsdvictim.player.team_index:
            return

        OnTakeDamage.manager.notify(avsdvictim, avsdattacker, info, time())
    else:
        avsdvictim = Player.from_index(index)

        OnTakeDamage.manager.notify(avsdvictim, None, info, time())


@EntityPreHook(EntityCondition.is_player, CBaseEntity.trace_attack.fget)
def pre_on_trace_attack(stack):
    info = make_object(TakeDamageInfo, stack[1])
    attacker = info.attacker

    if attacker != info.inflictor:
        return

    index = index_from_pointer(stack[0])

    if 0 < attacker <= global_vars.max_clients:
        if index == attacker:
            return

        avsdvictim = Player.from_index(index)
        avsdattacker = Player.from_index(attacker)

        if avsdattacker.player.team_index == avsdvictim.player.team_index:
            return

        OnTraceAttack.manager.notify(avsdvictim, avsdattacker, info)
    else:
        avsdvictim = Player.from_index(index)

        OnTraceAttack.manager.notify(avsdvictim, None, info)


# ============================================================================
# >> EVENTS
# ============================================================================
@Event('round_prestart')
def on_round_prestart(event):
    for delay in chain.from_iterable(_delays.values()):
        delay.cancel()

    _delays.clear()

    global _allow_abilities
    _allow_abilities = False


@Event('round_freeze_end')
def on_round_freeze_end(event):
    global _allow_abilities
    _allow_abilities = True


@Event('player_death')
def on_player_death(event):
    userid = event['userid']

    for delay in _delays[userid]:
        delay.cancel()

    del _delays[userid]
