from pathlib import Path
from gwas_sumstats_tools.utils import (append_to_path,
                                       parse_genome_assembly,
                                       replace_dictionary_keys,
                                       split_fields_on_delimiter)


def test_append_to_path():
    test_path = Path("./tests/utils_test/test.ext1")
    assert append_to_path(path=test_path, to_add="-ext2.ext3") == Path("./tests/utils_test/test.ext1-ext2.ext3")


def test_parse_genome_assembly():
    test_path = Path("./tests/utils_test/GCST123456_build37.tsv")
    assert parse_genome_assembly(test_path) == '37'
    test_path = Path("./tests/utils_test/GCST123456_Build37.tsv")
    assert parse_genome_assembly(test_path) == '37'
    test_path = Path("./tests/utils_test/GCST123456_GRCh37.tsv")
    assert parse_genome_assembly(test_path) == '37'
    test_path = Path("./tests/utils_test/GCST123456_grch37.tsv")
    assert parse_genome_assembly(test_path) == '37'


def test_replace_dictionary_keys():
    data_dict = {'a': 1, 'b': 2}
    replace_dict = {'a': 'A', 'b': 'B'}
    new_data_dict = replace_dictionary_keys(data_dict=data_dict,
                                            replace_dict=replace_dict)
    assert new_data_dict['A'] == 1
    assert new_data_dict['B'] == 2
    assert len(new_data_dict) == 2


def test_split_fields_on_delimiter():
    data_dict = {'a': "1|2|3", 'b': 2}
    new_data_dict = split_fields_on_delimiter(data_dict, tuple("a"))
    assert new_data_dict["a"] == ["1", "2", "3"]
