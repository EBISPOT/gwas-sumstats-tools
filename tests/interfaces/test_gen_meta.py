import gzip

import pytest

from gwas_sumstats_tools.gen_meta import Gen_meta

# https://www.ebi.ac.uk/gwas/ingest/api/v2/studies/GCST90013541
# https://www.ebi.ac.uk/gwas/rest/api/v2/studies/GCST006186

CASES = [
    # rest api
    {"case": 1,"accession": "GCST008396", "expected_min_ancestry_len": 1, "expected_min_EFO_len": 1, "expected_min_genotyping_technology": 1, "notes": "single ancestry", "api_call_from": "rest_api"},
    {"case": 2,"accession": "GCST006186", "expected_min_ancestry_len": 5, "expected_min_EFO_len": 2,"expected_min_genotyping_technology": 1, "notes": "multi ancestry",  "api_call_from": "rest_api"},
    {"case": 3,"accession": "GCST005544", "expected_min_ancestry_len": 1, "expected_min_EFO_len": 1,  "expected_min_genotyping_technology": 3, "notes": "multi ancestry", "api_call_from": "rest_api"},
    # ingest api
    {"case": 4,"accession": "GCST90018791", "expected_min_ancestry_len": 4, "expected_min_EFO_len": 1,"expected_min_genotyping_technology": 1, "notes": "multi ancestry",  "api_call_from": "ingest_api"},
    {"case": 5,"accession": "GCST90011787", "expected_min_ancestry_len": 1, "expected_min_EFO_len": 0, "expected_min_genotyping_technology": 2, "notes": "published study but no efo trait", "api_call_from": "ingest_api"},
    {"case": 6,"accession": "GCST90012203", "expected_min_ancestry_len": 1, "expected_min_EFO_len": 6, "expected_min_genotyping_technology": 1, "notes": " efo_trait : EFO_0004348,EFO_0004528,EFO_0004527,EFO_0004526,EFO_0004305,EFO_0005192","api_call_from": "ingest_api"},
    {"case": 7,"accession": "GCST90011807", "expected_min_ancestry_len": 1, "expected_min_EFO_len": 2,"expected_min_genotyping_technology": 1, "notes": "efo_trait:EFO_0002916|EFO_0000178", "api_call_from": "ingest_api"},
    {"case": 8,"accession": "GCST90435377", "expected_min_ancestry_len": 1, "expected_min_EFO_len": 2,"expected_min_genotyping_technology": 1, "notes": "efoTraits:[list,shortForm]", "api_call_from": "ingest_api"},
]


def _create_empty_gz(tmp_path, accession):
    infile = tmp_path / f"{accession}.tsv.gz"
    with gzip.open(infile, "wb") as fh:
        fh.write(b"")
    return infile


@pytest.mark.parametrize("case", CASES)
def test_gen_meta_api_lists(case, tmp_path):
    infile = _create_empty_gz(tmp_path, case["accession"])
    meta = Gen_meta(data_infile=infile).set_metadata(from_gwas_cat=True)
    meta_dict = meta.as_dict()
    print( meta)

    # EFO mapping should be a list when present
    ontology_mapping = meta_dict.get("ontology_mapping")
    assert ontology_mapping is not None
    assert isinstance(ontology_mapping, list)
    assert len(ontology_mapping) >= case["expected_min_EFO_len"]

    # Genotyping technology should be a list when present
    genotyping_technology = meta_dict.get("genotyping_technology")
    assert genotyping_technology is not None
    assert isinstance(genotyping_technology, list)
    assert len(genotyping_technology) >= case["expected_min_genotyping_technology"]

    # Samples should exist and ancestry should be a list on at least one sample
    samples = meta_dict.get("samples")
    print ("samples",samples)
    assert samples is not None
    assert len(samples) > 0    
    assert isinstance(samples, list)
    assert len(samples) >= case["expected_min_ancestry_len"]
    
