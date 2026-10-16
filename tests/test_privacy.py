from beanagileorg.core import privacy
from beanagileorg.core.privacy import Level, filter_record, filter_records, floor_for_scopes

privacy.register("sample", {"title": Level.EXPORTABLE, "detail": Level.PRESENTABLE, "notes": Level.PRIVATE})

RECORD = {"id": 1, "title": "[Placeholder title]", "detail": "[Placeholder detail]", "notes": "[Placeholder notes]"}


def test_private_floor_sees_everything():
    assert filter_record("sample", RECORD, Level.PRIVATE) == RECORD


def test_presentable_floor_hides_private_fields():
    assert filter_record("sample", RECORD, Level.PRESENTABLE) == {
        "id": 1,
        "title": "[Placeholder title]",
        "detail": "[Placeholder detail]",
    }


def test_exportable_floor_keeps_only_exportable():
    assert filter_record("sample", RECORD, Level.EXPORTABLE) == {"id": 1, "title": "[Placeholder title]"}


def test_untagged_fields_default_to_private():
    record = {**RECORD, "new_field": "[Placeholder]"}
    assert "new_field" not in filter_record("sample", record, Level.PRESENTABLE)


def test_record_ceiling_makes_a_record_more_private():
    presentable_only = {**RECORD, "privacy_ceiling": Level.PRESENTABLE}
    assert filter_record("sample", presentable_only, Level.EXPORTABLE) is None
    shown = filter_record("sample", presentable_only, Level.PRESENTABLE)
    assert shown == {"id": 1, "title": "[Placeholder title]", "detail": "[Placeholder detail]"}


def test_filter_records_drops_hidden_records():
    private = {**RECORD, "id": 2, "privacy_ceiling": Level.PRIVATE}
    assert [r["id"] for r in filter_records("sample", [RECORD, private], Level.PRESENTABLE)] == [1]


def test_scope_floors():
    assert floor_for_scopes(["export:read"]) == Level.EXPORTABLE
    assert floor_for_scopes(["export:read", "present:read"]) == Level.PRESENTABLE
    assert floor_for_scopes(["full"]) == Level.PRIVATE
    assert floor_for_scopes([]) == Level.EXPORTABLE
