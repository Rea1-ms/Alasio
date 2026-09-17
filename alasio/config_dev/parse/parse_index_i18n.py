import yaml

from alasio.config_dev.parse.base import DefinitionError
from alasio.ext.file.yamlfile import yaml_loads
from alasio.ext.path.atomic import atomic_read_bytes


def read_index_i18n(file):
    """Read optional, hand-maintained nav and queue labels outside generated indices."""
    try:
        raw = atomic_read_bytes(file)
    except FileNotFoundError:
        return {}
    try:
        data = yaml_loads(raw)
    except yaml.YAMLError as exc:
        raise DefinitionError(exc, file=file) from exc
    if type(data) is not dict:
        raise DefinitionError('Index i18n must be a dict', file=file, value=data)
    for section, rows in data.items():
        if section not in {'nav', 'queue'}:
            raise DefinitionError('Unknown index i18n section', file=file, keys=[section])
        if type(rows) is not dict:
            raise DefinitionError('Index i18n section must be a dict', file=file, keys=[section], value=rows)
        for name, languages in rows.items():
            keys = [section, name]
            if not isinstance(name, str) or not name:
                raise DefinitionError('Index i18n key must be a non-empty string', file=file, keys=keys)
            if type(languages) is not dict:
                raise DefinitionError('Index i18n languages must be a dict', file=file, keys=keys, value=languages)
            for lang, value in languages.items():
                if not isinstance(lang, str) or not lang:
                    raise DefinitionError('Index i18n language must be a non-empty string', file=file, keys=keys)
                if not isinstance(value, str):
                    raise DefinitionError(
                        'Index i18n label must be a string', file=file, keys=[*keys, lang], value=value)
    return data
