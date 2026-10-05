"""Error and warning code catalog.

Job-level errors abort a batch run (non-zero exit code) or reject an HTTP
request. Record-level errors only mark that one molecule as failed; the rest
of the input is still predicted. Warnings never block a prediction.
"""

# code: (HTTP status, batch exit code, default message)
ERRORS = {
    # job-level input errors
    "E-INPUT-001": (422, 2, "Input file not found or not readable"),
    "E-INPUT-003": (413, 2, "Too many molecules in one request"),
    "E-INPUT-004": (422, 2, "Unsupported input file format (use .csv, .sdf, .mol, .smi or .txt)"),
    "E-INPUT-005": (422, 2, "CSV input has no 'smiles' column"),
    "E-INPUT-006": (422, 2, "Input contains no molecules"),
    "E-INPUT-011": (422, 2, "Request body does not match the API schema"),
    # record-level input errors
    "E-INPUT-002": (422, None, "SMILES could not be parsed by RDKit"),
    "E-INPUT-007": (422, None, "Empty SMILES"),
    "E-INPUT-008": (422, None, "Molecule record in SDF/MOL could not be read"),
    "E-INPUT-009": (422, None, "No molecule left after standardization"),
    "E-INPUT-010": (422, None, "SMILES is longer than MAX_SMILES_LENGTH"),
    # model / system errors
    "E-MODEL-001": (503, 3, "Model or SE-encoder files could not be loaded"),
    "E-MODEL-002": (503, 3, "Model file checksum does not match SHA256SUMS"),
    "E-MODEL-003": (500, None, "SE encoder produced no usable tokens for this SMILES"),
    "E-SYS-001": (500, 4, "Output directory is not writable"),
    "E-SYS-002": (500, 4, "DEVICE=cuda was requested but no GPU is visible"),
    "E-SYS-003": (500, 4, "Unexpected internal error"),
    "E-SYS-004": (400, 4, "Invalid configuration value"),
}

WARNINGS = {
    "W-STD-001": "Multiple fragments (salt, solvent or mixture) in input",
    "W-STD-002": "Charged atoms in input (ionized form)",
    "W-STD-003": "Standardization changed the structure (largest fragment kept / charges neutralized)",
    "W-ENC-001": "SE encoder dropped or did not recognize part of the SMILES",
}


class ToxError(Exception):
    """An error with a catalog code. `detail` carries the specific reason."""

    def __init__(self, code: str, detail: str | None = None):
        self.code = code
        self.http_status, self.exit_code, self.message = ERRORS[code]
        self.detail = detail
        super().__init__(f"{code}: {self.message}" + (f" — {detail}" if detail else ""))

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "detail": self.detail}
