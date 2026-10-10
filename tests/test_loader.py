import pytest

from autoflow.loader import FileLoadError, load_file


def test_load_csv_from_path(csv_file, raw_orders):
    df = load_file(csv_file)
    assert list(df.columns) == list(raw_orders.columns)
    assert len(df) == len(raw_orders)
    assert df.loc[0, "order_id"] == "ORD-001"


def test_load_xlsx_from_path(xlsx_file, raw_orders):
    df = load_file(xlsx_file)
    assert len(df) == len(raw_orders)
    assert df.loc[1, "amount"] == "$1,250.00"


def test_load_from_bytes_requires_filename(csv_file):
    data = csv_file.read_bytes()
    assert len(load_file(data, filename="upload.csv")) == 8
    with pytest.raises(FileLoadError, match="extension"):
        load_file(data)


def test_values_kept_as_strings(tmp_path):
    path = tmp_path / "o.csv"
    path.write_text("order_id,customer_name,order_date,amount\n007,A,2024-01-01,10\n")
    df = load_file(path)
    assert df.loc[0, "order_id"] == "007"  # leading zero preserved


def test_headers_normalized(tmp_path):
    path = tmp_path / "o.csv"
    path.write_text(" Order_ID , Customer_Name,ORDER_DATE,Amount\n1,A,2024-01-01,10\n")
    df = load_file(path)
    assert list(df.columns) == ["order_id", "customer_name", "order_date", "amount"]


def test_latin1_csv(tmp_path):
    path = tmp_path / "o.csv"
    path.write_bytes("order_id,customer_name,order_date,amount\n1,Jos\xe9,2024-01-01,10\n".encode("latin-1"))
    assert load_file(path).loc[0, "customer_name"] == "José"


def test_empty_file(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    with pytest.raises(FileLoadError, match="empty"):
        load_file(path)


def test_whitespace_only_file(tmp_path):
    path = tmp_path / "blank.csv"
    path.write_text("   \n\n")
    with pytest.raises(FileLoadError):
        load_file(path)


def test_unsupported_extension(tmp_path):
    path = tmp_path / "orders.txt"
    path.write_text("a,b\n1,2\n")
    with pytest.raises(FileLoadError, match="Unsupported"):
        load_file(path)


def test_missing_file(tmp_path):
    with pytest.raises(FileLoadError, match="not found"):
        load_file(tmp_path / "nope.csv")


def test_corrupt_xlsx(tmp_path):
    path = tmp_path / "bad.xlsx"
    path.write_bytes(b"this is not really an excel file")
    with pytest.raises(FileLoadError, match="Excel"):
        load_file(path)


def test_malformed_csv(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text('order_id,customer_name\n1,"unterminated\n2,x\n')
    with pytest.raises(FileLoadError):
        load_file(path)


def test_loader_does_not_modify_input(csv_file):
    before = csv_file.read_bytes()
    load_file(csv_file)
    assert csv_file.read_bytes() == before
