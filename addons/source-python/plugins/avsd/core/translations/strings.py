# ../avsd/core/translations/strings.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
#   Configobj
from configobj import ConfigObj

# Source.Python Imports
#   Hooks
from hooks.exceptions import except_hooks
#   Translations
from translations.strings import TranslationStrings as _TranslationStrings

# AvsD Imports
#   Constants
from ..constants.paths import TRANSLATION_PATH


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (
    'LangStrings',
)


# =============================================================================
# >> CLASSES
# =============================================================================
class LangStrings(dict):
    def __init__(self, indir, encoding='utf8'):
        super().__init__()

        path = TRANSLATION_PATH.joinpath(indir)

        if not path.isdir():
            raise FileNotFoundError('No file found at {0}'.format(path))

        for languagepath in path.listdir():
            try:
                infile = ConfigObj(languagepath, encoding=encoding)
            except:
                except_hooks.print_exception()
            else:
                language = languagepath.namebase

                for key in infile:
                    if key not in self:
                        self[key] = TranslationStrings()

                    self._add_key(key, language, infile[key])

    def _add_key(self, key, language, text):
        self[key][language] = text


class TranslationStrings(_TranslationStrings):
    def get_string(self, language=None, **tokens):
        self.tokens.update(tokens)

        for token, value in self.tokens.items():
            if isinstance(value, TranslationStrings):
                self.tokens[token] = value.get_string(language)

        return super().get_string(language)
