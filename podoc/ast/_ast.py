# -*- coding: utf-8 -*-

"""Markup AST."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import logging

from six import string_types

from podoc.plugin import IPlugin
from podoc.utils import Bunch

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Utils
#------------------------------------------------------------------------------

def _remove_json_meta(d):
    if isinstance(d, dict):
        return {k: _remove_json_meta(v) for k, v in d.items() if k != 'm'}
    elif isinstance(d, list):
        return [_remove_json_meta(v) for v in d]
    else:
        return d


def ae(a, b):
    if isinstance(a, (list, dict)):
        assert _remove_json_meta(a) == _remove_json_meta(b)
    else:
        assert a == b


#------------------------------------------------------------------------------
# AST
#------------------------------------------------------------------------------

# List of allowed Pandoc block names.
PANDOC_BLOCK_NAMES = (
    'Plain',
    'Para',
    'CodeBlock',
    'RawBlock',
    'BlockQuote',
    'OrderedList',
    'BulletList',
    'DefinitionList',
    'Header',
    'HorizontalRule',
    'Table',
    'Div',
)


# List of allowed Pandoc inline names.
PANDOC_INLINE_NAMES = (
    'Str',
    'Emph',
    'Strong',
    'Strikeout',
    'Code',
    'Space',
    'LineBreak',
    'Math',
    'Link',
    'Image',
)


class AST(Bunch):
    """An AST (Abstract Syntax Tree) represents a complete markup document.

    * An AST contains a list of Blocks.
    * A Block has a name and a list of children. Every child is either:
      * A Block
      * An Inline
    * An Inline has a name and a list of children. Every child is either:
      * An Inline
      * A Python string

    """
    def __init__(self, *args, **kwargs):
        super(AST, self).__init__(*args, **kwargs)
        self.blocks = kwargs.pop('blocks', [])
        assert isinstance(self.blocks, list)

    def add_block(self, block):
        """Add a Block instance."""
        assert isinstance(block, Block)
        self.blocks.append(block)

    def to_dict(self):
        return [{'unMeta': {}},
                [block.to_dict() for block in self.blocks]]

    @staticmethod
    def from_dict(d):
        """Convert a pandoc-compatible dict to a podoc AST."""
        assert len(d) == 2
        blocks = [Block.from_dict(_) for _ in d[1]]
        return AST(blocks=blocks)


class Block(Bunch):
    def __init__(self, *args, **kwargs):
        super(Block, self).__init__(*args, **kwargs)
        self.name = kwargs.pop('name', 'Block')
        assert self.name in PANDOC_BLOCK_NAMES
        self.meta = kwargs.pop('meta', {})
        # List of either Block or Inline instances.
        self.children = kwargs.pop('children', [])
        Block._check_children(self.children)

    def add_metadata(self, **kwargs):
        self.meta.update(**kwargs)

    def add_child(self, child):
        """Add a Block or Inline child."""
        assert isinstance(child, (Block, Inline))
        self.children.append(child)

    @staticmethod
    def _check_children(children):
        assert isinstance(children, list)
        assert all(isinstance(child, (Block, Inline))
                   for child in children)

    def to_dict(self):
        Block._check_children(self.children)
        return {
            't': self.name,
            'm': self.meta,
            'c': [child.to_dict() for child in self.children]
        }

    @staticmethod
    def from_dict(d):
        name = d['t']
        # d can be a Block or an Inline.
        # Route to inline.
        if name in PANDOC_INLINE_NAMES:
            return Inline.from_dict(d)
        # Now, we really have a block.
        assert name in PANDOC_BLOCK_NAMES
        meta = d.get('m', {})
        children = d['c']
        children = [Block.from_dict(_) for _ in children]
        Block._check_children(children)
        return Block(name=name, meta=meta, children=children)


class Inline(Bunch):
    def __init__(self, *args, **kwargs):
        super(Inline, self).__init__(*args, **kwargs)
        self.name = kwargs.pop('name', 'Inline')
        assert self.name in PANDOC_INLINE_NAMES
        # This is always a list of dicts.
        self.children = kwargs.pop('children', [])
        Inline._check_children(self.children)

    def set_string(self, string):
        self.children = string

    def add_child(self, child):
        """Add an Inline or String child."""
        assert isinstance(self.children, list)
        assert isinstance(child, Inline)
        self.children.append(child)
        self._check_children(self.children)

    @staticmethod
    def _check_children(children):
        assert isinstance(children, (list, string_types))
        if isinstance(children, list):
            assert all(isinstance(child, Inline) for child in children)

    def to_dict(self):
        Inline._check_children(self.children)
        children = self.children
        if isinstance(children, list):
            children = [child.to_dict() for child in self.children]
        return {
            't': self.name,
            'c': children,
        }

    @staticmethod
    def from_dict(d):
        name = d['t']
        children = d['c']
        if isinstance(children, list):
            children = [Inline.from_dict(_) for _ in children]
        Inline._check_children(children)
        return Inline(name=name, children=children)


#------------------------------------------------------------------------------
# AST plugin
#------------------------------------------------------------------------------

class ASTPlugin(IPlugin):
    """The file format is JSON, same as the pandoc json format."""
    def attach(self, podoc):
        # An object in the language 'ast' is an instance of AST.
        podoc.register_lang('ast', file_ext='.json',
                            open_func=self.open, save_func=self.save)

    def open(self, path):
        """Open a .json file and return an AST instance."""
        logger.debug("Open JSON file `%s`.", path)
        with open(path, 'r') as f:
            ast_obj = json.load(f)
        assert isinstance(ast_obj, list)
        ast = AST.from_dict(ast_obj)
        assert isinstance(ast, AST)
        return ast

    def save(self, path, ast):
        """Save an AST instance to a JSON file."""
        assert isinstance(ast, AST)
        ast_obj = ast.to_dict()
        assert isinstance(ast_obj, list)
        logger.debug("Save JSON file `%s`.", path)
        with open(path, 'w') as f:
            json.dump(ast_obj, f, sort_keys=True, indent=2)
            # Add a new line at the end.
            f.write('\n')
