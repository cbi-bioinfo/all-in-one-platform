"""Input reading and SMILES preparation.

Default preparation matches how the trainset was built: RDKit parse + canonical
SMILES, nothing else (salts, counter-ions and charges were kept in the
trainset). Fragments and charges are reported as warnings. With
STANDARDIZE=1 the largest organic fragment is kept and charges are
neutralized before prediction.
"""
import csv
import logging
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from rdkit import Chem, rdBase
from rdkit.Chem.MolStandardize import rdMolStandardize

from .errors import ToxError

SUPPORTED_EXT = (".csv", ".sdf", ".mol", ".smi", ".txt")
ID_COLUMNS = ("id", "mol_id", "name", "compound_id")

rdBase.LogToPythonLogger()
_rdkit_logger = logging.getLogger("rdkit")
_rdkit_logger.propagate = False
_TIMESTAMP = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]\s*")


@dataclass
class Record:
    index: int
    record_id: str
    input_smiles: str | None
    error: ToxError | None = None


@dataclass
class Prepared:
    canonical_smiles: str
    warnings: list[str] = field(default_factory=list)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.lines: list[str] = []

    def emit(self, record):
        msg = _TIMESTAMP.sub("", record.getMessage()).strip()
        if msg and not msg.startswith("*"):
            self.lines.append(msg)


@contextmanager
def _rdkit_messages():
    handler = _Capture()
    _rdkit_logger.addHandler(handler)
    try:
        yield handler.lines
    finally:
        _rdkit_logger.removeHandler(handler)


# ── readers ───────────────────────────────────────────────────────────────────

def read_input(path: Path) -> list[Record]:
    if not path.is_file():
        raise ToxError("E-INPUT-001", str(path))
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXT:
        raise ToxError("E-INPUT-004", f"'{ext or path.name}'")
    try:
        if ext == ".csv":
            records = _read_csv(path)
        elif ext == ".sdf":
            records = _read_sdf(path)
        elif ext == ".mol":
            records = _read_mol(path)
        else:
            records = _read_lines(path)
    except UnicodeDecodeError as e:
        raise ToxError("E-INPUT-001", f"not a UTF-8 text file ({e.reason})")
    if not records:
        raise ToxError("E-INPUT-006", str(path))
    return records


def _read_csv(path: Path) -> list[Record]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        smi_col = next((c for c in fields if c.strip().lower() in ("smiles", "canonical_smiles")), None)
        if smi_col is None:
            raise ToxError("E-INPUT-005", f"columns found: {fields}")
        id_col = next((c for c in fields if c.strip().lower() in ID_COLUMNS), None)
        records = []
        for i, row in enumerate(reader):
            smi = (row.get(smi_col) or "").strip()
            rid = (row.get(id_col) or "").strip() if id_col else ""
            records.append(Record(i, rid or f"mol_{i}", smi))
    return records


def _read_lines(path: Path) -> list[Record]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            i = len(records)
            records.append(Record(i, parts[1] if len(parts) > 1 else f"mol_{i}", parts[0]))
    return records


def _read_sdf(path: Path) -> list[Record]:
    records = []
    with _rdkit_messages() as msgs:
        for i, mol in enumerate(Chem.SDMolSupplier(str(path))):
            if mol is None:
                err = ToxError("E-INPUT-008", f"record {i}: " + ("; ".join(msgs) or "unreadable"))
                records.append(Record(i, f"mol_{i}", None, err))
            else:
                rid = mol.GetProp("_Name").strip() if mol.HasProp("_Name") else ""
                records.append(Record(i, rid or f"mol_{i}", Chem.MolToSmiles(mol)))
            msgs.clear()
    return records


def _read_mol(path: Path) -> list[Record]:
    with _rdkit_messages() as msgs:
        mol = Chem.MolFromMolFile(str(path))
    if mol is None:
        return [Record(0, path.stem, None, ToxError("E-INPUT-008", "; ".join(msgs) or "unreadable"))]
    return [Record(0, path.stem, Chem.MolToSmiles(mol))]


def records_from_smiles(smiles: list[str], ids: list[str] | None = None) -> list[Record]:
    return [Record(i, (ids[i] if ids and i < len(ids) and ids[i] else f"mol_{i}"), (s or "").strip())
            for i, s in enumerate(smiles)]


# ── preparation ──────────────────────────────────────────────────────────────

def prepare(smiles: str, standardize: bool, max_length: int) -> Prepared:
    if not smiles:
        raise ToxError("E-INPUT-007")
    if len(smiles) > max_length:
        raise ToxError("E-INPUT-010", f"{len(smiles)} > {max_length} characters")

    with _rdkit_messages() as msgs:
        mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ToxError("E-INPUT-002", "; ".join(msgs) or "RDKit returned no molecule")
    if mol.GetNumAtoms() == 0:
        raise ToxError("E-INPUT-007", "SMILES contains no atoms")

    warnings = []
    if len(Chem.GetMolFrags(mol)) > 1:
        warnings.append("W-STD-001")
    if any(a.GetFormalCharge() != 0 for a in mol.GetAtoms()):
        warnings.append("W-STD-002")

    canonical = Chem.MolToSmiles(mol)
    if standardize and warnings:
        std = rdMolStandardize.LargestFragmentChooser(preferOrganic=True).choose(mol)
        std = rdMolStandardize.Uncharger().uncharge(std)
        if std is None or std.GetNumAtoms() == 0:
            raise ToxError("E-INPUT-009")
        std_smiles = Chem.MolToSmiles(std)
        if std_smiles != canonical:
            warnings.append("W-STD-003")
            canonical = std_smiles
    return Prepared(canonical, warnings)
