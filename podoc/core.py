# -*- coding: utf-8 -*-

"""Core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Utility functions
#------------------------------------------------------------------------------

def open_text(path):
    with open(path, 'r') as f:
        return f.read()


def save_text(path, contents):
    with open(path, 'w') as f:
        return f.write(contents)


class Podoc(object):
    """Conversion pipeline for markup documents.

    This class implements the core conversion functionality of podoc.

    """
    file_opener = None
    preprocessors = None
    reader = None
    filters = None
    writer = None
    postprocessors = None
    file_saver = None

    def __init__(self):
        if self.preprocessors is None:
            self.preprocessors = []
        if self.filters is None:
            self.filters = []
        if self.postprocessors is None:
            self.postprocessors = []

    # Individual stages
    # -------------------------------------------------------------------------

    def open(self, path):
        if self.file_opener is None:
            self.file_opener = open_text
        assert self.file_opener is not None
        return self.file_opener(path)

    def save(self, path, contents):
        if self.file_saver is None:
            self.file_saver = save_text
        assert self.file_saver is not None
        return self.file_saver(path, contents)

    def preprocess(self, contents):
        for p in self.preprocessors:
            contents = p(contents)
        return contents

    def read(self, contents):
        if self.reader is None:
            logger.warn("No reader set")
            return contents
        assert self.reader is not None
        ast = self.reader(contents)
        return ast

    def filter(self, ast):
        for f in self.filters:
            ast = f(ast)
        return ast

    def write(self, ast):
        if self.writer is None:
            logger.warn("No writer set")
            return ast
        assert self.writer is not None
        converted = self.writer(ast)
        return converted

    def postprocess(self, contents):
        for p in self.postprocessors:
            contents = p(contents)
        return contents

    # Main methods
    # -------------------------------------------------------------------------

    def convert_file(self, from_path, to_path=None):
        document = self.open(from_path)
        converted = self.convert_contents(document)
        return self.save(to_path, converted) if to_path else converted

    def convert_contents(self, contents):
        contents = self.preprocess(contents)
        ast = self.read(contents)
        ast = self.filter(ast)
        converted = self.write(ast)
        converted = self.postprocess(converted)
        return converted

    # Pipeline configuration
    # -------------------------------------------------------------------------

    def set_file_opener(self, func):
        """A file opener is a function `str (path)` -> `str (or object)`.

        The output may be a string or another type of object, like a file
        handle, etc.

        """
        self.file_opener = func
        return self

    def add_preprocessor(self, func):
        self.preprocessors.append(func)
        return self

    def set_reader(self, func):
        """A reader is a function `str (or object)` -> `ast`.

        The input corresponds to the output of the file opener.

        """
        self.reader = func
        return self

    def add_filter(self, func):
        self.filters.append(func)
        return self

    def set_writer(self, func):
        """A reader is a function `ast` -> `str (or object)`.

        The output corresponds to the input of the file saver.

        """
        self.writer = func
        return self

    def add_postprocessor(self, func):
        self.postprocessors.append(func)
        return self

    def set_file_saver(self, func):
        """A file saver is a function `str (path), str (or object) -> None`.

        The second input corresponds to the output of the writer.

        """
        self.file_saver = func
        return self

    # Plugins
    # -------------------------------------------------------------------------

    def set_plugins(self, plugins=(), plugins_from=(), plugins_to=()):
        plugins = [P() for P in plugins]
        plugins_from = [P() for P in plugins_from]
        plugins_to = [P() for P in plugins_to]

        for p in plugins:
            p.register(self)

        for p in plugins_from:
            p.register_from(self)

        for p in plugins_to:
            p.register_to(self)

        return self
