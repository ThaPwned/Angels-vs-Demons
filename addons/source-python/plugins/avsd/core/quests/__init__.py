# ../avsd/core/quests/__init__.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Collections
from collections import defaultdict
#   Itertools
from itertools import chain

# Schedule Imports
#   Schedule
from schedule import Scheduler

# AvsD Imports
#   Config
from ..config import quests_data
#   Constants
# from ..constants import MENU_MISSING_TEXT
from ..constants import QUEST_RESET_REGEX
#   Database
from ..database.manager import database_manager
#   Listeners
# from ..listeners import OnPlayerDelete
# from ..listeners import OnPlayerSwitchClassPost
from ..listeners import OnQuestComplete
from ..listeners import OnQuestReset
from ..listeners import OnRequirementComplete
#   Translations
from ..translations.strings import LangStrings


# ============================================================================
# >> GLOBAL VARIABLES
# ============================================================================
scheduler = Scheduler()
# rewards_queue = defaultdict(lambda: defaultdict(int))


# ============================================================================
# >> CLASSES
# ============================================================================
class _Quest(object):
    def __init__(self, name, rewards, format_, reset, strings, _id=None):
        self.name = name
        self.rewards = rewards
        self.format = format_
        self._requirements = defaultdict(list)
        self.strings = strings

        if 'name' in strings:
            self._name = 'name'
        else:
            self._name = 'name' if _id is None else 'name ' + _id

        if 'description' in strings:
            self._description = 'description'
        else:
            self._description = 'description' if _id is None else 'description ' + _id

        job = None
        current_method = None

        if reset is not None:
            for method, arguments in QUEST_RESET_REGEX.findall(reset + '.do'):
                if current_method is None:
                    current_method = getattr(scheduler, method)
                else:
                    current_method = getattr(current_method, method)

                if arguments == '()':
                    current_method = current_method()
                elif arguments.startswith('(') and arguments.endswith(')'):
                    current_method = current_method(arguments[1:-1])
                elif method == 'do':
                    current_method(self.reset)

                if job is None:
                    job = current_method

        self._job = job

    def get_format(self):
        data = defaultdict(int)

        for name, value in self.format.items():
            for requirement in self.requirements:
                if requirement.name == value:
                    data[name] += requirement.count

        return data

    def get_progress(self, player):
        return [(require, require.get_progress(player)) for require in self.requirements]

    def get_progress_percentage(self, player, clean=True):
        requirements = self.requirements

        percentage = sum(require.get_progress_percentage(player, False) for require in requirements) / len(requirements)

        if clean:
            # return ('%.2f' % percentage).rstrip('0').rstrip('.')
            return f'{percentage:0.2f}'.rstrip('0').rstrip('.')

        return percentage

    def is_completed(self, player):
        return all(require.is_completed(player) for require in self.requirements)

    def reset(self):
        OnQuestReset.manager.notify()

        from ..players.filters import PlayerIter

        for _, player in PlayerIter():
            quest = player.quests[self.name]
            quest['completed'] = 0

            for requirement in quest['requirements']:
                quest['requirements'][requirement] = 0

        database_manager.execute('quest reset', (self.name, ))
        database_manager.execute('requirement reset', (self.name, ))

    @property
    def requirements(self):
        return list(chain.from_iterable(self._requirements.values()))


class _Requirement(object):
    def __init__(self, quest, name, count, data):
        self._quest = quest

        self.name = name
        self.count = count
        self.data = data

    def get_progress(self, player):
        return player.quests[self._quest.name]['requirements'][self.name]

    def get_progress_percentage(self, player, clean=True):
        progress = self.get_progress(player)

        if progress >= self.count:
            return 100

        percentage = progress / self.count * 100

        if clean:
            # return ('%.2f' % percentage).rstrip('0').rstrip('.')
            return f'{percentage:0.2f}'.rstrip('0').rstrip('.')

        return percentage

    def is_completed(self, player):
        return self.get_progress(player) >= self.count

    def increase(self, player, counter=1):
        if self.is_completed(player):
            return

        value = self.get_progress(player) + counter

        if value > self.count:
            value = self.count

        player.quests[self._quest.name]['requirements'][self.name] = value

        if self.is_completed(player):
            OnRequirementComplete.manager.notify(player, self._quest, self)

            if self._quest.is_completed(player):
                OnQuestComplete.manager.notify(player, self._quest)

                player.inbox.receive(f'_quest_complete_{self._quest.name}', rewards=dict(self._quest.rewards.items()))

                # if player.active_class is None:
                #     for name, value in self._quest.rewards.items():
                #         rewards_queue[player][name] += value
                # else:
                #     for name, value in self._quest.rewards.items():
                #         setattr(player, name, getattr(player, name) + value)


class _RequirementsContainer(list):
    def increase(self, player, counter=1):
        if not player._is_bot:
            for requirement in self:
                requirement.increase(player, counter)


class _QuestManager(dict):
    def __init__(self):
        super().__init__()

        self._requirements = defaultdict(list)

        for quest_name, data in quests_data.items():
            # try:
            strings = LangStrings('quests_strings/{0}'.format(quest_name))
            # except FileNotFoundError:
            #     strings = defaultdict(lambda: MENU_MISSING_TEXT)

            if 'count' in data:
                real_rewards = data.get('rewards', {})
                reset = data.get('reset')
                quests = []

                for i in range(data['count']):
                    quest_name = quest_name + '-' + str(i)
                    rewards = real_rewards.copy()

                    for name, value in real_rewards.items():
                        if isinstance(value, list):
                            value = rewards[name] = value[i]

                        if not value:
                            del rewards[name]

                    quest = self[quest_name] = _Quest(quest_name, rewards, data.get('format'), reset[i] if isinstance(reset, list) else reset, strings, str(i))

                    quests.append(quest)

                    for requirement_data in data['requirements']:
                        type_ = requirement_data.get('type')
                        require_name = requirement_data.get('name', type_)
                        count = requirement_data.get('count')

                        if isinstance(count, list):
                            count = count[i]

                        requirement = _Requirement(quest, require_name, count, {key:value for key, value in requirement_data.items() if key not in ('type', 'name', 'count')})

                        quest._requirements[type_].append(requirement)
                        self._requirements[type_].append(requirement)
            else:
                quest = self[quest_name] = _Quest(quest_name, data.get('rewards', {}), data.get('format'), data.get('reset'), strings)

                for requirement_data in data['requirements']:
                    type_ = requirement_data.pop('type')
                    require_name = requirement_data.pop('name', type_)
                    count = requirement_data.pop('count')

                    requirement = _Requirement(quest, require_name, count, requirement_data)

                    quest._requirements[type_].append(requirement)
                    self._requirements[type_].append(requirement)

    def get_requirements(self, type_, **kwargs):
        requirements = _RequirementsContainer()

        if kwargs:
            for requirement in self._requirements[type_]:
                if all([requirement.data.get(keyword) == equal_to for keyword, equal_to in kwargs.items()]):
                    requirements.append(requirement)
        else:
            for requirement in self._requirements[type_]:
                if not requirement.data:
                    requirements.append(requirement)

        return requirements

    def get_dynamic_requirements(self, type_):
        requirements = self._requirements[type_]

        def inner(**kwargs):
            new_requirements = _RequirementsContainer()

            if kwargs:
                for requirement in requirements:
                    if all([requirement.data.get(keyword) == equal_to for keyword, equal_to in kwargs.items()]):
                        new_requirements.append(requirement)
            else:
                for requirement in requirements:
                    if not requirement.data:
                        new_requirements.append(requirement)

            return new_requirements

        return inner
quest_manager = _QuestManager()


# ============================================================================
# >> LISTENERS
# ============================================================================
# @OnPlayerDelete
# def on_player_delete(avsdplayer):
#     rewards = rewards_queue.pop(avsdplayer, None)

#     if rewards is not None:
#         if avsdplayer.current_class is not None:
#             for name, value in rewards.items():
#                 setattr(avsdplayer, name, getattr(avsdplayer, name) + value)


# @OnPlayerSwitchClassPost
# def on_player_switch_class_post(avsdplayer, old, new):
#     if new is not None:
#         rewards = rewards_queue.pop(avsdplayer, None)

#         if rewards is not None:
#             for name, value in rewards.items():
#                 setattr(avsdplayer, name, getattr(avsdplayer, name) + value)
