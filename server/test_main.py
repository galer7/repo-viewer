import pytest
from fastapi.testclient import TestClient
import tempfile
import os
from pathlib import Path

# Import the FastAPI app from your main file
# Assuming your main file is named 'main.py'
from main import app

client = TestClient(app)


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create a simple Python file in the temporary directory
        test_file_content = """
class TestClass:
    def test_method(self):
        pass

def test_function():
    pass
        """
        file_path = Path(tmpdirname) / "test_file.py"
        file_path.write_text(test_file_content)

        yield tmpdirname


def test_visualize_endpoint(temp_repo):
    response = client.post("/visualize", json={"path": temp_repo})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1  # We only created one file

    file_data = data[0]
    assert file_data["filename"].endswith("test_file.py")

    # Check if the class is correctly identified
    assert len(file_data["classes"]) == 1
    assert file_data["classes"][0]["name"] == "TestClass"

    # Check if the method is correctly identified
    assert len(file_data["classes"][0]["methods"]) == 1
    assert file_data["classes"][0]["methods"][0]["name"] == "test_method"

    # Check if the function is correctly identified
    assert len(file_data["functions"]) == 1
    assert file_data["functions"][0]["name"] == "test_function"


def test_visualize_endpoint_invalid_path():
    response = client.post("/visualize", json={"path": "/invalid/path"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid repository path"


def test_visualize_endpoint_empty_repo(temp_repo):
    # Remove all .py files from the temporary directory
    for file in Path(temp_repo).glob("*.py"):
        os.remove(file)

    response = client.post("/visualize", json={"path": temp_repo})
    assert response.status_code == 200
    assert response.json() == []  # Empty list when no Python files are found


def test_visualize_endpoint_parse_error(temp_repo):
    # Create a Python file with invalid syntax
    invalid_file_content = """
    This is not valid Python syntax
    """
    file_path = Path(temp_repo) / "invalid_file.py"
    file_path.write_text(invalid_file_content)

    response = client.post("/visualize", json={"path": temp_repo})
    assert response.status_code == 200
    assert response.json() == []  # Should return an empty list on parse error
