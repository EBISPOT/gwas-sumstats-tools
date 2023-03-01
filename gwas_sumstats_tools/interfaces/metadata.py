import yaml
from typing import Union
from datetime import date
from pathlib import Path
from gwas_sumstats_tools.utils import (download_with_requests,
                                       parse_accession_id,
                                       parse_genome_assembly,
                                       get_md5sum)
from gwas_sumstats_tools.schema.metadata import SumStatsMetadata


GWAS_CAT_API_STUDIES_URL = "https://www.ebi.ac.uk/gwas/rest/api/studies/"
GWAS_CAT_MAPPINGS = {
    'genotypingTechnology': 'genotypingTechnology',
    'sampleSize': 'sampleSize',
    'sampleAncestry': 'sampleAncestry',
    'traitDescription': 'traitDescription',
    'effectAlleleFreqLowerLimit': 'effectAlleleFreqLowerLimit',
    'ancestryMethod': 'ancestryMethod',
    'caseControlStudy': 'caseControlStudy',
    'caseCount': 'caseCount',
    'controlCount': 'controlCount',
    'genomeAssembly': 'genomeAssembly',
    'pvalueIsNegLog10': 'pvalueIsNegLog10',
    'analysisSoftware': 'analysisSoftware',
    'imputationPanel': 'imputationPanel',
    'imputationSoftware': 'imputationSoftware',
    'adjustedCovariates': 'adjustedCovariates',
    'ontologyMapping': 'ontologyMapping',
    'authorNotes': 'authorNotes',
    'coordinateSystem': 'coordinateSystem',
    'sex': 'sex'
    }
GENOME_ASSEMBLY_MAPPINGS = {
    '36': 'GRCh36',
    '37': 'GRCh37',
    '38': 'GRCh38'
    }


class MetadataClient:
    def __init__(self, meta_dict: dict = {},
                 in_file: Path = None,
                 out_file: Path = None) -> None:
        """SumStats Metadata client

        Keyword Arguments:
            meta_dict -- Dict of metadata (default: {None})
            in_file -- Input metadata YAML file (default: {None})
            out_file -- Output metadata YAML file (default: {None})
        """
        self.metadata = SumStatsMetadata.construct()
        self._meta_dict = meta_dict
        self._in_file = in_file
        self._out_file = out_file

    def from_file(self) -> None:
        """Create metadata from YAML file
        """
        with open(self._in_file, "r") as fh:
            self._meta_dict = yaml.safe_load(fh)
            self.update_metadata(self._meta_dict)

    def to_file(self) -> None:
        """Write metadata to YAML file
        """
        with open(self._out_file, "w") as fh:
            yaml.dump(self.metadata.dict(exclude_none=True),
                      fh,
                      encoding='utf-8')

    def update_metadata(self, data_dict: dict) -> None:
        """Create a copy of the model and update (no validation occurs)

        Arguments:
            data_dict -- Dict of data to populate model
        """
        self._meta_dict.update(data_dict)
        self.metadata = self.metadata.parse_obj(self._meta_dict)

    def __repr__(self) -> str:
        """YAML str representation of metadata.
        """
        return yaml.dump(self.metadata.dict())

    def as_dict(self) -> dict:
        """Dict repr of metadata

        Returns:
            Dict of metadata
        """
        return self.metadata.dict()


def metadata_dict_from_args(args: list) -> dict:
    """Generate a dict from cli args split on "="

    Arguments:
        args -- cli args list

    Returns:
        Dict of key, values
    """
    meta_dict = {}
    for arg in args:
        if "=" not in arg:
            # skip because it's not a metadata mapping
            pass
        else:
            key, value = arg.replace("--", "").split("=")
            meta_dict[key] = value
    return meta_dict


def metadata_dict_from_gwas_cat(accession_id: str) -> dict:
    """Extract metadat from the GWAS Catalog API

    Arguments:
        accession_id -- GWAS Catalog accession ID

    Returns:
        Metadata dict
    """
    study_url = GWAS_CAT_API_STUDIES_URL + accession_id
    content = download_with_requests(url=study_url)
    meta_dict = {}
    # TODO parse content into meta_dict
    return meta_dict


def get_file_metadata(in_file: Path, out_file: str) -> dict:
    """Get file related metadata

    Arguments:
        in_file -- sumstats in file
        outfile -- sumstats out file

    Returns:
        Metadata dict
    """
    meta_dict = {}
    accession_id = parse_accession_id(filename=in_file) 
    meta_dict['GWASID'] = accession_id
    meta_dict['dataFileName'] = Path(out_file).name
    meta_dict['fileType'] = 'GWAS-SFF v0.1'
    meta_dict['genomeAssembly'] = GENOME_ASSEMBLY_MAPPINGS.get(parse_genome_assembly(filename=in_file), 'unknown')
    meta_dict['dataFileMd5sum'] = get_md5sum(out_file) if Path(out_file).exists() else None
    meta_dict['dateLastModified'] = date.today()
    meta_dict['GWASCatalogAPI'] = GWAS_CAT_API_STUDIES_URL + accession_id
    return meta_dict


def init_metadata_from_file(filename: Path, metadata_infile: Path = None) -> Union[SumStatsMetadata, None]:
    m_in = metadata_infile if metadata_infile else filename.with_suffix(filename.suffix + "-meta.yaml")
    if m_in.exists():
        ssm = MetadataClient(in_file=m_in)
        ssm.from_file()
        return ssm
    else:
        return None