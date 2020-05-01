from app.db.queries.tables import TypedTable


def test_typed_table_uses_explicit_name() -> None:
    assert TypedTable("table_name").get_sql() == "table_name"


def test_typed_table_use_class_attribute_as_table_name() -> None:
    class NewTable(TypedTable):
        __table__ = "new_table"

    assert NewTable().get_table_name() == "new_table"


def test_typed_table_use_class_name_as_table_name() -> None:
    class NewTable(TypedTable):
        ...

    assert NewTable().get_table_name() == "NewTable"
