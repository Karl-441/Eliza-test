import os
import pytest
from server.core.tools import execute_tool, AVAILABLE_TOOLS

def test_tool_registry():
    assert "create_word_doc" in AVAILABLE_TOOLS
    assert "create_excel_sheet" in AVAILABLE_TOOLS
    assert "create_ppt" in AVAILABLE_TOOLS

def test_create_word_doc():
    filename = "test_doc.docx"
    content = "# Title\n\nThis is a test document."
    result = execute_tool("create_word_doc", filename=filename, content=content, title="Main Title")
    assert "Document saved" in result
    
    path = os.path.join("data", "outputs", filename)
    assert os.path.exists(path)
    # Cleanup
    try:
        os.remove(path)
    except:
        pass

def test_create_excel_sheet():
    filename = "test_sheet.xlsx"
    data = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
    result = execute_tool("create_excel_sheet", filename=filename, data=data)
    assert "Excel sheet saved" in result
    
    path = os.path.join("data", "outputs", filename)
    assert os.path.exists(path)
    # Cleanup
    try:
        os.remove(path)
    except:
        pass

def test_create_ppt():
    filename = "test_slides.pptx"
    slides = [
        {"title": "Slide 1", "content": "Point 1\nPoint 2"},
        {"title": "Slide 2", "content": "Conclusion"}
    ]
    result = execute_tool("create_ppt", filename=filename, slides=slides)
    assert "Presentation saved" in result
    
    path = os.path.join("data", "outputs", filename)
    assert os.path.exists(path)
    # Cleanup
    try:
        os.remove(path)
    except:
        pass
