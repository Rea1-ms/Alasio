from alasio.config.entry.const import ConfigConst, ModEntryInfo
from alasio.config.entry.model import DECODER_CACHE, MOD_JSON_CACHE, MODEL_CONFIG_INDEX, MODEL_TASK_INDEX
from alasio.ext.cache import cached_property
from alasio.ext import env
from alasio.ext.file.loadpy import LOADPY_CACHE
from alasio.ext.path import PathStr
from alasio.logger import logger


class ModBase:
    def __init__(self, entry: ModEntryInfo):
        """
        Args:
            entry: Mod entry info
        """
        self.entry = entry
        self.name = entry.name
        self.root = PathStr.new(entry.root)
        self.path_config = self.root.joinpath(entry.path_config)
        self.path_assets = self.root.joinpath(entry.path_assets)
        alasio = ModEntryInfo.alasio()
        self.path_alasio_config = env.ALASIO_ROOT.joinpath(alasio.path_config)

    def __str__(self):
        """
        Mod(name="alasio", root="E:/ProgramData/Pycharm/Alasio/alasio")
        """
        return f'{self.__class__.__name__}(name="{self.name}", root="{self.root.to_posix()}")'

    def __bool__(self):
        return True

    @cached_property
    def config_const(self):
        """Load the optional constants and GUI hooks declared by this mod."""
        file = self.path_config / 'const.py'
        try:
            module = LOADPY_CACHE.get(file)
        except ImportError as e:
            logger.warning(
                f'DataInconsistent: failed to import config constants "{file}": {e}')
            return ConfigConst
        config_const = getattr(module, 'ConfigConst', None)
        if config_const is None:
            logger.warning(
                f'DataInconsistent: Missing ConfigConst in "{file}"')
            return ConfigConst
        return config_const

    @staticmethod
    def _gui_config_paths(values) -> "frozenset[tuple[str, str, str]]":
        paths = set()
        for value in values:
            if not isinstance(value, str):
                continue
            path = tuple(value.split('.', 2))
            if len(path) == 3:
                paths.add(path)
        return frozenset(paths)

    @cached_property
    def gui_config_hidden_targets(self) -> "frozenset[tuple[str, str, str]]":
        values = getattr(self.config_const, 'GUI_CONFIG_HIDDEN_TARGETS', ())
        return self._gui_config_paths(values)

    @cached_property
    def gui_config_hidden_dependencies(self) -> "frozenset[tuple[str, str, str]]":
        values = getattr(self.config_const, 'GUI_CONFIG_HIDDEN_DEPENDENCIES', ())
        return self._gui_config_paths(values)

    def gui_config_hidden(self, data) -> "set[str]":
        handler = getattr(self.config_const, 'gui_config_hidden', None)
        if not callable(handler):
            return set()
        try:
            values = handler(data)
        except Exception as e:
            logger.exception(
                f'DataInconsistent: failed to evaluate GUI visibility for mod "{self.name}": {e}')
            return set()
        return {value for value in values if isinstance(value, str)}

    """
    Index json
    """

    def nav_index_data(self):
        """
        Returns:
            dict[str, dict[str, dict[str, Any]]]:
                key: {nav_name}.{card_name}
                value:
                    {"i18n": {lang: name}} for normal cards
                    {"scheduler": True, "i18n": {lang: name}} for cards with scheduler
        """
        file = self.path_config.joinpath('_index/nav.index.json')
        decoder = DECODER_CACHE.MODEL_DICT_DEPTH3_ANY
        return MOD_JSON_CACHE.get(file, decoder=decoder)

    def queue_index_data(self):
        """
        Returns:
            dict[str, dict[str, str]]:
                key: {task_name}.{lang}
                value: i18n translation
        """
        file = self.path_config.joinpath('_index/queue.index.json')
        decoder = DECODER_CACHE.MODEL_DICT_DEPTH2_ANY
        return MOD_JSON_CACHE.get(file, decoder=decoder)

    def config_index_data(self) -> MODEL_CONFIG_INDEX:
        """
        """
        file = self.path_config.joinpath('_index/config.index.json')
        decoder = DECODER_CACHE.MODEL_CONFIG_INDEX
        return MOD_JSON_CACHE.get(file, decoder=decoder)

    def task_index_data(self) -> MODEL_TASK_INDEX:
        """
        """
        file = self.path_config.joinpath('_index/task.index.json')
        decoder = DECODER_CACHE.MODEL_TASK_INDEX
        return MOD_JSON_CACHE.get(file, decoder=decoder)

    def nav_config_json(self, file):
        """
        Args:
            file (str): relative path to {nav}_config.json

        Returns:
            dict[str, dict[str, dict]]:
                key: {card_name}.{arg_name}
                value:
                    {"group": group, "arg": "_info"} for _info
                    {"task": task, "group": group, "arg": arg, **ArgData.to_dict()} for normal args
                        which is arg path appended with ArgData
        """
        if file.startswith('alasio/'):
            file = self.path_alasio_config / file
        else:
            file = self.path_config / file
        decoder = DECODER_CACHE.MODEL_DICT_DEPTH3_ANY
        return MOD_JSON_CACHE.get(file, decoder=decoder)

    def nav_i18n_json(self, file):
        """
        Args:
            file (str): relative path to {nav}_i18n.json

        Returns:
            dict[str, dict[str, dict[str, dict[str, Any]]]]:
                key: {group_name}.{arg_name}.{lang}.{field}
                    where field is "name", "help", "option_i18n", etc.
                value: translation
        """
        if file.startswith('alasio/'):
            file = self.path_alasio_config / file
        else:
            file = self.path_config / file
        decoder = DECODER_CACHE.MODEL_DICT_DEPTH3_ANY
        return MOD_JSON_CACHE.get(file, decoder=decoder)

    def get_group_model(self, file, cls):
        """
        Get msgspec validation model

        Args:
            file (str): relative path to {nav}_model.py from path_config
            cls (str): class name

        Returns:
            Type[msgspec.Struct] | None:
        """
        if file.startswith('alasio/'):
            file = self.path_alasio_config / file
        else:
            file = self.path_config / file
        try:
            module = LOADPY_CACHE.get(file)
        except ImportError as e:
            # DataInconsistent error.
            # We just log warnings to reduce runtime crash, missing config will fall back to default
            logger.warning(
                f'DataInconsistent: failed to import model.py "{file}": {e}')
            return None
        model = getattr(module, cls, None)
        if model is None:
            logger.warning(
                f'DataInconsistent: Missing class "{cls}" in "{file}"')
            return None
        return model
