from __future__ import annotations

from types import ModuleType


def test_exact_match_wins(mobapp_resolver: ModuleType) -> None:
    result = mobapp_resolver.resolve_mobapp_dname(
        "gary_iphone", ["gary_iphone", "gary_ipad"])
    assert result == ("gary_iphone", mobapp_resolver.EXACT)


def test_renamed_suffix_is_healed(mobapp_resolver: ModuleType) -> None:
    # HA renamed foo -> foo_2 after an entity id collision.
    result = mobapp_resolver.resolve_mobapp_dname("foo_2", ["foo", "bar"])
    assert result == ("foo", mobapp_resolver.RENAMED)


def test_original_name_is_healed_to_suffixed_entity(
        mobapp_resolver: ModuleType) -> None:
    result = mobapp_resolver.resolve_mobapp_dname("foo", ["foo_2", "bar"])
    assert result == ("foo_2", mobapp_resolver.RENAMED)


def test_two_candidates_are_ambiguous(mobapp_resolver: ModuleType) -> None:
    result = mobapp_resolver.resolve_mobapp_dname(
        "foo_2", ["foo", "foo_3"])
    assert result == (None, mobapp_resolver.AMBIGUOUS)


def test_never_uses_a_reserved_tracker(mobapp_resolver: ModuleType) -> None:
    result = mobapp_resolver.resolve_mobapp_dname(
        "foo_2", ["foo"], reserved_dnames={"foo"})
    assert result == (None, mobapp_resolver.RESERVED)


def test_prefix_is_not_a_match(mobapp_resolver: ModuleType) -> None:
    # The old ScanFor logic used startswith and could attach foobar to foo.
    result = mobapp_resolver.resolve_mobapp_dname("foo", ["foobar"])
    assert result == (None, mobapp_resolver.NOT_FOUND)


def test_duplicate_suffix_forms_are_ambiguous(
        mobapp_resolver: ModuleType) -> None:
    result = mobapp_resolver.resolve_mobapp_dname(
        "foo_9", ["foo", "foo (2)"])
    assert result == (None, mobapp_resolver.AMBIGUOUS)


def test_disabled_candidate_is_not_used(mobapp_resolver: ModuleType) -> None:
    result = mobapp_resolver.resolve_mobapp_dname(
        "foo_2", ["foo"], disabled_dnames={"foo"})
    assert result == (None, mobapp_resolver.DISABLED)


def test_empty_name_is_invalid(mobapp_resolver: ModuleType) -> None:
    assert mobapp_resolver.resolve_mobapp_dname("", ["foo"]) == (
        None, mobapp_resolver.INVALID)
    assert mobapp_resolver.resolve_mobapp_dname("None", ["foo"]) == (
        None, mobapp_resolver.INVALID)


def test_suffix_base_removes_only_one_duplicate_suffix(
        mobapp_resolver: ModuleType) -> None:
    assert mobapp_resolver.mobapp_dname_base("foo_2") == "foo"
    assert mobapp_resolver.mobapp_dname_base("foo (2)") == "foo"
    assert mobapp_resolver.mobapp_dname_base("foo_2_3") == "foo_2"
    assert mobapp_resolver.mobapp_dname_base("foo") == "foo"


def test_candidates_are_not_mutated(mobapp_resolver: ModuleType) -> None:
    candidates = ["foo", "bar"]
    mobapp_resolver.resolve_mobapp_dname("foo_2", candidates)
    assert candidates == ["foo", "bar"]
