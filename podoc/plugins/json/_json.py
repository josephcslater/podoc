# -*- coding: utf-8 -*-

"""JSON plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import logging

from podoc.ast import from_json, to_json
from podoc.plugin import IPlugin

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# JSON plugin
#------------------------------------------------------------------------------

class JSON(IPlugin):
    file_extensions = ('.json',)

    def _open_json(self, path):
        logger.debug("Open JSON file `%s`.", path)
        with open(path, 'r') as f:
            return json.load(f)

    def _read_json_file(self, contents):
        return from_json(contents)

    def _write_json(self, ast):
        return to_json(ast)

    def _save_json(self, path, contents):
        logger.debug("Save JSON file `%s`.", path)
        json.dump(contents, path, sort_keys=True, indent=2)
        return contents

    def register_from(self, podoc):
        # path -> file_handle
        podoc.set_opener(self._open_json)
        # file_handle -> AST
        podoc.set_reader(self._read_json_file)

    def register_to(self, podoc):
        # AST -> json dict
        podoc.set_writer(self._write_json)
        # path, json_dict -> None
        podoc.set_saver(self._save_json)