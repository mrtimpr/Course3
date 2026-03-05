from src.file_store import read_json, write_json


def test_write_and_read_json(tmp_path):
    p = tmp_path / "data.json"
    data = {"a": 1, "b": {"c": [1, 2, 3]}}

    write_json(p, data)
    loaded = read_json(p)

    assert loaded == data
