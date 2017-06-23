# -*- coding: utf-8 -*-

"""Test Notebook plugin."""


#-------------------------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------------------------

import os.path as op
import re

from podoc.markdown import MarkdownPlugin
from podoc.utils import get_test_file_path, load_text
from podoc.ast import ASTPlugin, ASTNode
from .._notebook import (_get_b64_resource,
                         extract_output,
                         output_filename,
                         open_notebook,
                         NotebookReader,
                         NotebookWriter,
                         wrap_code_cells,
                         )


#-------------------------------------------------------------------------------------------------
# Test Notebook utils
#-------------------------------------------------------------------------------------------------

def test_get_b64_resource():
    assert not _get_b64_resource(None)
    assert len(_get_b64_resource(b'abcdef')) >= 4


def test_extract_output():
    # Open a test notebook with a code cell containing an image.
    path = get_test_file_path('notebook', 'simplenb.ipynb')
    notebook = open_notebook(path)
    cell = notebook.cells[4]
    mime_type, data = list(extract_output(cell.outputs[1]))
    filename = output_filename(mime_type, cell_index=4, output_index=1)
    assert filename == 'output_4_1.png'

    # Open the image file in the markdown directory.
    image_path = get_test_file_path('markdown', 'simplenb_files/' + filename)
    with open(image_path, 'rb') as f:
        data_expected = f.read()

    # The two image contents should be identical.
    assert data == data_expected


def test_wrap_code_cells_1():
    # Test wrap_code_cells() with a single code cell.
    ast = ASTNode('root')
    ast.add_child(ASTNode('CodeBlock', lang='python', children=['']))

    ast_wrapped = wrap_code_cells(ast)
    ast_wrapped.show()

    ast_expected = ASTNode('root')
    ast_expected.add_child(ASTNode('CodeCell', children=[ast.children[0]]))

    assert ast_wrapped == ast_expected


def test_wrap_code_cells_2():
    # Test wrap_code_cells() with two code cells.
    ast = ASTNode('root')

    cb0 = ASTNode('CodeBlock', lang='python', children=['a'])
    cb1 = ASTNode('CodeBlock', lang='python', children=['b'])

    ast.add_child(cb0)
    ast.add_child(cb1)

    ast.show()
    ast_wrapped = wrap_code_cells(ast)
    ast_wrapped.show()

    ast_expected = ASTNode('root')

    # First code cell.
    code_cell0 = ASTNode('CodeCell')
    code_cell0.add_child(cb0)
    ast_expected.add_child(code_cell0)

    # Second code cell.
    code_cell1 = ASTNode('CodeCell')
    code_cell1.add_child(cb1)
    ast_expected.add_child(code_cell1)
    ast_expected.show()

    assert ast_wrapped == ast_expected


#-------------------------------------------------------------------------------------------------
# Test NotebookReader
#-------------------------------------------------------------------------------------------------

def test_notebook_reader_hello():
    # Open a test notebook with just 1 Markdown cell.
    path = get_test_file_path('notebook', 'hello.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    ast = NotebookReader().read(notebook)
    ast.show()
    # Check that the AST is equal to the one of a simple Mardown line.
    ast_1 = MarkdownPlugin().read('hello *world*')
    assert ast == ast_1


def test_notebook_reader_notebook():
    # Open a test notebook with a code cell.
    path = get_test_file_path('notebook', 'simplenb.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    reader = NotebookReader()
    ast = reader.read(notebook)
    ast.show()

    # Compare with the markdown version.
    path = get_test_file_path('markdown', 'simplenb.md')
    markdown_expected = load_text(path)
    markdown_converted = MarkdownPlugin().write(ast)
    markdown_converted = re.sub(r'\{resource:([^\}]+)\}', r'simplenb_files/\1',
                                markdown_converted)
    # The test file has a trailing new line, but not the AST.
    markdown_converted += '\n'
    assert markdown_converted == markdown_expected

    assert 'output_4_1.png' in reader.resources


#-------------------------------------------------------------------------------------------------
# Test NotebookWriter
#-------------------------------------------------------------------------------------------------

def test_notebook_empty():
    ast = ASTNode('root')
    ast.add_child(ASTNode('Para'))
    nb = NotebookWriter().write(ast)
    reader = NotebookReader()
    ast = reader.read(nb)
    assert not ast.children


def test_notebook_writer_hello():
    path = get_test_file_path('ast', 'hello.json')
    ast = ASTPlugin().load(path)
    nb = NotebookWriter().write(ast)

    # Compare the notebooks.
    nb_expected = open_notebook(get_test_file_path('notebook', 'hello.ipynb'))
    # Ignore some fields when comparing the notebooks.
    assert nb == nb_expected


def test_notebook_writer_notebook():
    path = get_test_file_path('ast', 'simplenb.json')
    ast = ASTPlugin().load(path)
    # TODO: save resource files in JSON serializer

    # Load the image.
    fn = get_test_file_path('markdown', 'simplenb_files/output_4_1.png')
    with open(fn, 'rb') as f:
        img = f.read()
    # Convert the AST to a notebook.
    nb = NotebookWriter().write(ast, context={'resources': {op.basename(fn): img}, 'path': path})

    # Compare the notebooks.
    nb_expected = open_notebook(get_test_file_path('notebook', 'simplenb.ipynb'))
    # Ignore some fields when comparing the notebooks.
    assert nb == nb_expected
