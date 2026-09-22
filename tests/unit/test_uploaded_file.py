from utils.uploaded_file import temp_file_from_bytes


def test_writes_bytes_and_yields_path():
    data = b"%PDF-1.4 fake content"

    with temp_file_from_bytes(data, suffix=".pdf") as path:
        assert path.exists()
        assert path.suffix == ".pdf"
        assert path.read_bytes() == data


def test_deletes_file_after_context_exits():
    with temp_file_from_bytes(b"some bytes") as path:
        pass

    assert not path.exists()


def test_deletes_file_even_on_exception():
    captured_path = None

    try:
        with temp_file_from_bytes(b"some bytes") as path:
            captured_path = path
            raise ValueError("boom")
    except ValueError:
        pass

    assert not captured_path.exists()
