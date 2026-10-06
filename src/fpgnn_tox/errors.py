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
    "E-INPUT-004": (422, 2, "Unsupported input file format (use .csv, .txt, .sdf or .mol)"),
    "E-INPUT-005": (422, 2, "CSV input has no 'smiles' column"),
    "E-INPUT-006": (422, 2, "Input contains no molecules"),
    "E-INPUT-011": (422, 2, "Request body does not match the API schema"),
    "E-INPUT-012": (413, 2, "Uploaded job input is larger than JOB_MAX_UPLOAD_MB"),
    # record-level input errors
    "E-INPUT-002": (422, None, "SMILES could not be parsed by RDKit"),
    "E-INPUT-007": (422, None, "Empty SMILES"),
    "E-INPUT-008": (422, None, "Molecule record in SDF/MOL could not be read"),
    "E-INPUT-009": (422, None, "No molecule left after standardization"),
    "E-INPUT-010": (422, None, "SMILES is longer than MAX_SMILES_LENGTH"),
    # model / system errors
    "E-MODEL-001": (503, 3, "Model files could not be loaded"),
    "E-MODEL-002": (503, 3, "Model file checksum does not match SHA256SUMS"),
    "E-MODEL-003": (500, None, "Molecule could not be converted to a graph"),
    "E-SYS-001": (500, 4, "Output directory is not writable"),
    "E-SYS-002": (500, 4, "DEVICE=cuda was requested but no GPU is visible"),
    "E-SYS-003": (500, 4, "Unexpected internal error"),
    "E-SYS-004": (400, 4, "Invalid configuration value"),
    "E-SYS-005": (503, None, "Model is still loading (retry when GET /readyz returns 200)"),
    # job API (serve mode)
    "E-JOB-001": (404, None, "Job not found"),
    "E-JOB-002": (409, None, "Job result is not available (job not completed)"),
}

WARNINGS = {
    "W-STD-001": "Multiple fragments (salt, solvent or mixture) in input",
    "W-STD-002": "Charged atoms in input (ionized form)",
    "W-STD-003": "Standardization changed the structure (largest fragment kept / charges neutralized)",
    "W-FEAT-001": "Some atom properties are outside the categories of the atom encoder and were encoded in its 'other' slot",
    "W-FEAT-002": "Molecule has atoms without bonds (e.g. isolated ions); their graph attention spans all atoms",
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
