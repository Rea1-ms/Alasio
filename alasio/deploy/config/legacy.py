"""Compatibility reader for legacy ALAS-style deploy configuration."""

from copy import deepcopy

import msgspec
import yaml
from alasio.ext.file.yamlconfig import iter_yaml_rows
from alasio.ext.file.yamlfile import yaml_dumps, yaml_loads
from alasio.ext.path.atomic import atomic_read_text, atomic_write
from alasio.logger import logger
from msgspec import NODEFAULT
from msgspec.msgpack import encode as msgpack_encode
from msgspecerror import load_msgpack_with_default

_MISSING = object()

# Current model path -> legacy ``Deploy`` path. Every field in DeployModel is
# covered so validated changes can always be persisted without creating a
# second configuration file.
LEGACY_PATHS = {
    ('Repo', 'Repository'): ('Deploy', 'Git', 'Repository'),
    ('Repo', 'Branch'): ('Deploy', 'Git', 'Branch'),
    ('Repo', 'GitExecutable'): ('Deploy', 'Git', 'GitExecutable'),
    ('Repo', 'GitProxy'): ('Deploy', 'Git', 'GitProxy'),
    ('Repo', 'SSLVerify'): ('Deploy', 'Git', 'SSLVerify'),
    ('Python', 'PythonExecutable'): ('Deploy', 'Python', 'PythonExecutable'),
    ('Python', 'PypiMirror'): ('Deploy', 'Python', 'PypiMirror'),
    ('Python', 'InstallDependencies'): ('Deploy', 'Python', 'InstallDependencies'),
    ('Python', 'RequirementsFile'): ('Deploy', 'Python', 'RequirementsFile'),
    ('Adb', 'AdbExecutable'): ('Deploy', 'Adb', 'AdbExecutable'),
    ('Adb', 'ReplaceAdb'): ('Deploy', 'Adb', 'ReplaceAdb'),
    ('Adb', 'AutoConnect'): ('Deploy', 'Adb', 'AutoConnect'),
    ('Adb', 'InstallUiautomator2'): ('Deploy', 'Adb', 'InstallUiautomator2'),
    ('Ocr', 'UseOcrServer'): ('Deploy', 'Ocr', 'UseOcrServer'),
    ('Ocr', 'StartOcrServer'): ('Deploy', 'Ocr', 'StartOcrServer'),
    ('Ocr', 'OcrServerPort'): ('Deploy', 'Ocr', 'OcrServerPort'),
    ('Ocr', 'OcrClientAddress'): ('Deploy', 'Ocr', 'OcrClientAddress'),
    ('Update', 'AutoUpdate'): ('Deploy', 'Git', 'AutoUpdate'),
    ('Update', 'CheckUpdateInterval'): ('Deploy', 'Update', 'CheckUpdateInterval'),
    ('Update', 'AutoRestartTime'): ('Deploy', 'Update', 'AutoRestartTime'),
    ('Misc', 'DiscordRichPresence'): ('Deploy', 'Misc', 'DiscordRichPresence'),
    ('RemoteAccess', 'EnableRemoteAccess'): (
        'Deploy', 'RemoteAccess', 'EnableRemoteAccess'),
    ('RemoteAccess', 'SSHUser'): ('Deploy', 'RemoteAccess', 'SSHUser'),
    ('RemoteAccess', 'SSHServer'): ('Deploy', 'RemoteAccess', 'SSHServer'),
    ('RemoteAccess', 'SSHExecutable'): ('Deploy', 'RemoteAccess', 'SSHExecutable'),
    ('Backend', 'Host'): ('Deploy', 'Webui', 'WebuiHost'),
    ('Backend', 'Port'): ('Deploy', 'Webui', 'WebuiPort'),
    ('Backend', 'Password'): ('Deploy', 'Webui', 'Password'),
    ('Backend', 'WebuiSSLKey'): ('Deploy', 'Webui', 'WebuiSSLKey'),
    ('Backend', 'WebuiSSLCert'): ('Deploy', 'Webui', 'WebuiSSLCert'),
    ('Webapp', 'Lang'): ('Deploy', 'Webui', 'Language'),
    ('Webapp', 'Theme'): ('Deploy', 'Webui', 'Theme'),
    ('Webapp', 'DpiScaling'): ('Deploy', 'Webui', 'DpiScaling'),
}


def _read_repository(value):
    if value in {'global', 'cn'}:
        return 'https://github.com/Rea1-ms/AutoEpicSeven'
    return value


def _read_theme(value):
    if value == 'default':
        return 'light'
    return value


def _read_ssh_executable(value):
    return value or 'ssh'


READ_CONVERTERS = {
    ('Repo', 'Repository'): _read_repository,
    ('RemoteAccess', 'SSHExecutable'): _read_ssh_executable,
    ('Webapp', 'Theme'): _read_theme,
}

WRITE_CONVERTERS = {
    ('Webapp', 'Theme'): lambda value: 'default' if value == 'light' else value,
}


def _get_path(data, path):
    value = data
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return _MISSING
        value = value[key]
    return value


def _set_path(data, path, value):
    target = data
    for key in path[:-1]:
        child = target.get(key)
        if not isinstance(child, dict):
            child = {}
            target[key] = child
        target = child
    target[path[-1]] = value


def _legacy_to_current(raw):
    data = {}
    for current_path, legacy_path in LEGACY_PATHS.items():
        value = _get_path(raw, legacy_path)
        if value is _MISSING:
            continue
        converter = READ_CONVERTERS.get(current_path)
        if converter is not None:
            value = converter(value)
        _set_path(data, current_path, value)
    return data


def _yaml_scalar(value):
    text = yaml.safe_dump(
        value,
        allow_unicode=True,
        default_flow_style=True,
        sort_keys=False,
    )
    lines = [line for line in text.splitlines() if line != '...']
    if len(lines) != 1:
        raise ValueError(f'Expected a scalar deploy value, got {value!r}')
    return lines[0]


def _replace_yaml_scalars(text, updates):
    rows = []
    found = set()
    for path, row in iter_yaml_rows(text):
        if path in updates:
            key = row.split(':', 1)[0]
            row = f'{key}: {_yaml_scalar(updates[path])}'
            found.add(path)
        rows.append(row)
    result = '\n'.join(rows)
    if rows:
        result += '\n'
    return result, set(updates) - found


def is_legacy_deploy_config(file):
    """Return whether ``file`` uses the legacy top-level ``Deploy`` section."""
    try:
        raw = yaml_loads(atomic_read_text(file))
    except (FileNotFoundError, UnicodeDecodeError, yaml.YAMLError):
        return False
    return isinstance(raw, dict) and isinstance(raw.get('Deploy'), dict)


class LegacyDeployYamlConfig:
    """YamlConfig-compatible view over a legacy deploy file.

    Reads expose the current DeployModel. Writes translate only changed model
    fields back to their original legacy paths, preserving the legacy schema,
    comments, and all fields which have no current equivalent.
    """

    def __init__(self, file, model):
        self.file = file
        self.model = model
        self.errors = []
        self._source_text = ''
        self._raw = {}
        self.data = self.read()

    @staticmethod
    def _log_errors(errors):
        for error in errors:
            logger.warning(f'Invalid deploy config value: {error}')

    def read(self):
        try:
            self._source_text = atomic_read_text(self.file)
            raw = yaml_loads(self._source_text)
        except (FileNotFoundError, UnicodeDecodeError, yaml.YAMLError) as error:
            self.errors = [error]
            self.data = self.model()
            self._baseline = msgspec.to_builtins(self.data)
            self._log_errors(self.errors)
            return self.data

        if not isinstance(raw, dict) or not isinstance(raw.get('Deploy'), dict):
            error = ValueError('Legacy deploy config must contain a Deploy mapping')
            self.errors = [error]
            self.data = self.model()
            self._baseline = msgspec.to_builtins(self.data)
            self._log_errors(self.errors)
            return self.data

        self._raw = raw
        source = _legacy_to_current(raw)
        obj, errors = load_msgpack_with_default(msgpack_encode(source), self.model)
        if obj is NODEFAULT:
            obj = self.model()
        self.errors = errors
        if errors:
            self._log_errors(errors)
        self.data = obj
        self._baseline = msgspec.to_builtins(obj)
        logger.info(f'Loaded legacy deploy config compatibility view: {self.file}')
        return self.data

    def validate(self):
        try:
            self.data = msgspec.convert(msgspec.to_builtins(self.data), self.model)
        except Exception as error:
            self.errors = [error]
            self._log_errors(self.errors)
            return False
        self.errors = []
        return True

    def set(self, key, value):
        path = tuple(key)
        if path not in LEGACY_PATHS:
            error = KeyError(f'Key path {path!r} has no legacy deploy mapping')
            self.errors = [error]
            self._log_errors(self.errors)
            return False

        data = msgspec.to_builtins(self.data)
        _set_path(data, path, value)
        try:
            self.data = msgspec.convert(data, self.model)
        except Exception as error:
            self.errors = [error]
            self._log_errors(self.errors)
            return False
        self.errors = []
        return True

    def write(self, skip_same=True):
        current = msgspec.to_builtins(self.data)
        updates = {}
        for current_path, legacy_path in LEGACY_PATHS.items():
            before = _get_path(self._baseline, current_path)
            after = _get_path(current, current_path)
            if before == after:
                continue
            converter = WRITE_CONVERTERS.get(current_path)
            if converter is not None:
                after = converter(after)
            updates[legacy_path] = after

        if not updates:
            return False

        raw = deepcopy(self._raw)
        for path, value in updates.items():
            _set_path(raw, path, value)

        text, missing = _replace_yaml_scalars(self._source_text, updates)
        if missing:
            # Partial legacy files are valid. When a changed key was absent,
            # fall back to a full serialization so the value is not silently
            # discarded. Existing complete deploy files keep all comments.
            text = yaml_dumps(raw).decode('utf-8')
        if skip_same and text == self._source_text:
            return False

        logger.info(f'Write legacy deploy config {self.file}')
        atomic_write(self.file, text)
        self._source_text = text
        self._raw = raw
        self._baseline = current
        return True

    def show(self):
        logger.info(f'Showing legacy deploy config of {self.file}')
        default = msgspec.to_builtins(self.model())
        current = msgspec.to_builtins(self.data)
        count = 0
        for path in LEGACY_PATHS:
            before = _get_path(default, path)
            after = _get_path(current, path)
            if before == after:
                continue
            logger.info(f'  {".".join(path)} = {after!r}')
            count += 1
        if count:
            logger.info('(rest of the config is the same as default)')
        else:
            logger.info('(config is the same as default)')
