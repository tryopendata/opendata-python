from __future__ import annotations

from opendata_sdk._sql import normalize_sql, parse_dataset_refs

# -- parse_dataset_refs ---------------------------------------------------


def test_parse_bare_slash():
    refs = parse_dataset_refs("SELECT * FROM fred/gdp")
    assert refs == [("fred", "gdp")]


def test_parse_quoted_slash():
    refs = parse_dataset_refs('SELECT * FROM "fred/gdp"')
    assert refs == [("fred", "gdp")]


def test_parse_dot_form():
    refs = parse_dataset_refs("SELECT * FROM fred.gdp")
    assert refs == [("fred", "gdp")]


def test_parse_multiple_refs_with_join():
    sql = "SELECT a.year, b.pop FROM fred/gdp a JOIN census/pop b ON a.year = b.year"
    refs = parse_dataset_refs(sql)
    assert len(refs) == 2
    assert ("fred", "gdp") in refs
    assert ("census", "pop") in refs


def test_parse_compound_join_types():
    sql = "SELECT * FROM fred/gdp a LEFT JOIN census/pop b ON a.year = b.year"
    refs = parse_dataset_refs(sql)
    assert len(refs) == 2
    assert ("census", "pop") in refs


def test_parse_case_insensitive():
    refs = parse_dataset_refs("select * from fred/gdp")
    assert refs == [("fred", "gdp")]


def test_parse_no_refs():
    refs = parse_dataset_refs("SELECT 1")
    assert refs == []


def test_parse_deduplication():
    sql = "SELECT * FROM fred/gdp a JOIN fred/gdp b ON a.year = b.year"
    refs = parse_dataset_refs(sql)
    assert refs == [("fred", "gdp")]


def test_parse_hyphenated_names():
    refs = parse_dataset_refs("SELECT * FROM bls/cpi-u")
    assert refs == [("bls", "cpi-u")]


def test_parse_underscore_names():
    refs = parse_dataset_refs("SELECT * FROM my_provider/my_dataset")
    assert refs == [("my_provider", "my_dataset")]


def test_parse_dot_with_quoted_dataset():
    refs = parse_dataset_refs('SELECT * FROM fred."cpi-u"')
    assert refs == [("fred", "cpi-u")]


# -- normalize_sql --------------------------------------------------------


def test_normalize_bare_slash_gets_quoted():
    result = normalize_sql("SELECT * FROM fred/gdp")
    assert 'FROM "fred/gdp"' in result


def test_normalize_dot_form_converts():
    result = normalize_sql("SELECT * FROM fred.gdp")
    assert 'FROM "fred/gdp"' in result


def test_normalize_already_quoted_stays():
    sql = 'SELECT * FROM "fred/gdp"'
    result = normalize_sql(sql)
    assert result == sql


def test_normalize_mixed_forms():
    sql = "SELECT * FROM fred/gdp a JOIN census.pop b ON a.year = b.year"
    result = normalize_sql(sql)
    assert 'FROM "fred/gdp"' in result
    assert 'JOIN "census/pop"' in result


def test_normalize_join_clauses():
    sql = "SELECT * FROM fred/gdp JOIN bls/cpi-u ON 1=1"
    result = normalize_sql(sql)
    assert 'FROM "fred/gdp"' in result
    assert 'JOIN "bls/cpi-u"' in result


def test_normalize_preserves_rest_of_query():
    sql = "SELECT year, value FROM fred/gdp WHERE year > 2020 ORDER BY year"
    result = normalize_sql(sql)
    assert result == 'SELECT year, value FROM "fred/gdp" WHERE year > 2020 ORDER BY year'


def test_normalize_case_insensitive():
    result = normalize_sql("select * from fred/gdp")
    assert 'from "fred/gdp"' in result
