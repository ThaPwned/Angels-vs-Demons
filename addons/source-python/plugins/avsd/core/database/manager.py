# ../avsd/core/database/manager.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Configobj
from configobj import ConfigObj
#   PyMySQL
try:
    from pymysql import connect as mysql_connect
except ImportError:
    mysql_connect = None
#   SQLite3
from sqlite3 import connect as sqlite_connect

# Source.Python Imports
#   Translations
from translations.manager import language_manager

# AVSD Imports
#   Constants
from ..constants.paths import CFG_PATH
from ..constants.paths import DATA_PATH
from ..constants.paths import STRUCTURE_PATH
#   Database
from .thread import _queue
from .thread import _thread
from .thread import _repeat
#   Translations
from ..translations import config_strings


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (
    'database_manager',
    'statements',
)


# ============================================================================
# >> CONFIGURATION
# ============================================================================
_path = CFG_PATH.joinpath('database.ini')
_database = ConfigObj(_path, unrepr=True)

if not _path.isfile():
    _database['driver'] = 'sqlite'
    _database['host'] = 'localhost'
    _database['database'] = 'avsd_database'
    _database['user'] = 'root'
    _database['password'] = ''
    _database['timeout'] = 60
    _database['port'] = 3306

    _database.comments['driver'] = [config_strings['database driver'].get_string(language_manager.default)]
    _database.comments['host'] = [config_strings['database host'].get_string(language_manager.default)]
    _database.comments['database'] = [config_strings['database database'].get_string(language_manager.default)]
    _database.comments['user'] = [config_strings['database user'].get_string(language_manager.default)]
    _database.comments['password'] = [config_strings['database password'].get_string(language_manager.default)]
    _database.comments['timeout'] = [config_strings['database timeout'].get_string(language_manager.default)]
    _database.comments['port'] = [config_strings['database port'].get_string(language_manager.default)]

    _database.write()


# ============================================================================
# >> CLASSES
# ============================================================================
class _DatabaseManager(object):
    def __init__(self):
        # self._index = 1
        self._unloading = False

    def _put(self, query, arguments, callback, many, keywords):
        # self._index += 1

        # _queue.put((self._index, query, arguments or tuple(), callback, many, keywords))
        _queue.put((query, arguments or tuple(), callback, many, keywords))

    def execute(self, key, arguments=None, callback=None, **keywords):
        self._put(statements[key], arguments, callback, False, keywords)

    def execute_text(self, query, arguments=None, callback=None, **keywords):
        self._put(query, arguments, callback, False, keywords)

    def executemany(self, key, arguments=None, callback=None, **keywords):
        self._put(statements[key], arguments, callback, True, keywords)

    def executemany_text(self, query, arguments=None, callback=None, **keywords):
        self._put(query, arguments, callback, True, keywords)

    def callback(self, callback, **keywords):
        self._put(None, None, callback, False, keywords)

    def connect(self):
        _thread.start()
        _repeat.start(0.1)

    def close(self):
        self._put(None, None, None, False, None)

    def cleanup(self):
        self.execute('item cleanup')
database_manager = _DatabaseManager()


if _database['driver'].lower() == 'mysql':
    if mysql_connect is None:
        raise NotImplementedError('PyMySQL is not installed.')

    statements = ConfigObj(STRUCTURE_PATH.joinpath('mysql.ini'))

    # _queue.put((0, lambda: mysql_connect(host=_database['host'], port=_database['port'], user=_database['user'], passwd=_database['password'], connect_timeout=_database['timeout'])))
    _queue.put(lambda: mysql_connect(host=_database['host'], port=_database['port'], user=_database['user'], passwd=_database['password'], connect_timeout=_database['timeout']))

    database_manager.execute_text(statements['create database'] % _database['database'])
    database_manager.execute_text(statements['use database'] % _database['database'])
else:
    statements = ConfigObj(STRUCTURE_PATH.joinpath('sqlite.ini'))

    # _queue.put((0, lambda: sqlite_connect(DATA_PATH.joinpath('players.sqlite'))))
    _queue.put(lambda: sqlite_connect(DATA_PATH.joinpath('players.sqlite')))

for statement in sorted([x for x in statements if x.startswith('create')]):
    database_manager.execute(statement)
