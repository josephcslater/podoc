# -*- coding: utf-8 -*-

"""Test Notebook plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from podoc.markdown import Markdown
from podoc.utils import get_test_file_path, open_text, assert_equal
from podoc.ast import ASTPlugin, ASTNode
from .._notebook import (extract_output,
                         output_filename,
                         open_notebook,
                         NotebookReader,
                         NotebookWriter,
                         wrap_code_cells,
                         )


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Test Notebook
#------------------------------------------------------------------------------

def test_extract_output():
    # Open a test notebook with a code cell containing an image.
    path = get_test_file_path('notebook', 'image.ipynb')
    notebook = open_notebook(path)
    cell = notebook.cells[1]
    mime_type, data = list(extract_output(cell.outputs[0]))
    filename = output_filename(mime_type, cell_index=1, output_index=0)
    assert filename == 'output_1_0.png'

    # Open the image file in the markdown directory.
    image_path = get_test_file_path('markdown', filename)
    with open(image_path, 'rb') as f:
        data_expected = f.read()

    # The two image contents should be identical.
    assert data == data_expected


#------------------------------------------------------------------------------
# Test NotebookReader
#------------------------------------------------------------------------------

def test_notebook_reader_hello():
    # Open a test notebook with just 1 Markdown cell.
    path = get_test_file_path('notebook', 'hello.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    ast = NotebookReader().read(notebook)
    ast.show()
    # Check that the AST is equal to the one of a simple Mardown line.
    ast_1 = Markdown().read_markdown('hello *world*')
    assert ast == ast_1


def test_notebook_reader_code():
    # Open a test notebook with a code cell.
    path = get_test_file_path('notebook', 'code.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    ast = NotebookReader().read(notebook)
    ast.show()

    # Compare with the markdown version.
    path = get_test_file_path('markdown', 'code.md')
    markdown = open_text(path)
    assert_equal(Markdown().write_markdown(ast), markdown)


def test_notebook_reader_image():
    # Open a test notebook with a code cell.
    path = get_test_file_path('notebook', 'image.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    reader = NotebookReader()
    ast = reader.read(notebook)
    ast.show()

    # Compare with the markdown version.
    path = get_test_file_path('markdown', 'image.md')
    markdown = open_text(path)
    assert_equal(Markdown().write_markdown(ast), markdown)

    assert 'output_1_0.png' in reader.resources


#------------------------------------------------------------------------------
# Test NotebookWriter
#------------------------------------------------------------------------------

def test_notebook_writer_code():
    path = get_test_file_path('ast', 'code.json')
    ast = ASTPlugin().open(path)
    nb = NotebookWriter().write(ast)

    # Compare the notebooks.
    nb_expected = open_notebook(get_test_file_path('notebook', 'code.ipynb'))
    # Ignore some fields when comparing the notebooks.
    assert_equal(nb, nb_expected, ('metadata', 'kernelspec'))


def test_notebook_writer_image():
    path = get_test_file_path('ast', 'image.json')
    ast = ASTPlugin().open(path)

    # Load the image.
    fn = get_test_file_path('markdown', 'output_1_0.png')
    with open(fn, 'rb') as f:
        img = f.read()
    resources = {op.basename(fn): img}
    # Convert the AST to a notebook.
    nb = NotebookWriter().write(ast, resources=resources)

    # Compare the notebooks.
    nb_expected = open_notebook(get_test_file_path('notebook', 'image.ipynb'))
    # Ignore some fields when comparing the notebooks.
    assert_equal(nb, nb_expected, ('metadata', 'kernelspec'))


#------------------------------------------------------------------------------
# Test wrap code cells
#------------------------------------------------------------------------------

def test_wrap_code_cells_1():
    path = get_test_file_path('ast', 'code.json')
    ast = ASTPlugin().open(path)
    ast.show()

    ast_wrapped = wrap_code_cells(ast)
    ast_wrapped.show()

    assert len(ast_wrapped.children) == 3
    cell = ast_wrapped.children[2]
    assert cell.name == 'CodeCell'
    for i in range(3):
        assert cell.children[i] == ast.children[i + 2]


def test_wrap_code_cells_2():
    path = get_test_file_path('ast', 'image.json')
    ast = ASTPlugin().open(path)
    ast.show()

    ast_wrapped = wrap_code_cells(ast)
    ast_wrapped.show()

    # The blocks 1 and 2 should be wrapped: one input cell and one output
    # cell with an image.
    ast_expected = ASTNode('root')
    ast_expected.add_child(ast.children[0])
    ast_expected.children.append(ASTNode('CodeCell',
                                         children=ast.children[1:3]))
    ast_expected.add_child(ast.children[-1])
