import logging
import math
from dataclasses import dataclass,field
from email import errors
from typing import Any
from src import config
from src.exceptions import DataValidationError

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class FieldRule:
    """Describe what a valid value of one field looks like """
    name : str
    kind : str
    required : bool = False
    min_value : float | None = None
    max_value : float | None = None

COIN_RULES : tuple[FieldRule,...] = (
    FieldRule("id","str",required=True),
    FieldRule("symbol","str",required=True),
    FieldRule("name","str",required=True),
    FieldRule("current_price","number",required=True),
    FieldRule("market_cap","number",min_value=0),
    FieldRule("market_cap_rank","int",min_value=1),
    FieldRule("total_volume","number",min_value=0),
    FieldRule("high_24h","number",min_value = 0),
    FieldRule("low_24h","number",min_value = 0),
    FieldRule("price_change_percentage","number",min_value=-100),
    FieldRule("circulating_supply","number",min_value=0),
    FieldRule("last_updated","str"),
)

@dataclass
class RejectedRecord:
    """A raw record that failed validation, with the reasons"""
    raw : Any
    errors : list[str]

    @property
    def label(self) -> str:
        """short name for logs"""
        if isinstance(self.raw, dict):
            return str(self.raw.get("id","<no id>"))
        return "<not an object>"

@dataclass
class ValidationReport:
    """The outcome of validating one batch"""
    valid : list[dict] = field(default_factory=list)
    rejected : list[RejectedRecord] = field(default_factory=list)

    @property
    def total(self) -> int:
        return  len(self.valid) + len(self.rejected)

    @property
    def rejected_ratio(self) -> float:
        return len(self.rejected) / self.total if self.total else 0.0

def _is_number(value:Any) -> bool:
    """True for reL int/float values"""
    return isinstance(value ,(int,float)) and not isinstance(value,bool)

def _check_field(rule: FieldRule, value:Any) ->str | None:
    """Returns an error message if value breaks one rule"""
    if rule.kind == "str":
        if not isinstance(value,str):
            return f"{rule.name}: expected text, got{type(value).__name__}"
        if rule.required and not  value.strip():
            return f"{rule.name}: must not be empty"
        return None

    if rule.kind == "int":
        is_right_type = isinstance(value,int) and not isinstance(value,bool)
        expected = "a whole number"
    else:
        is_right_type = _is_number(value)
        expected = "a number"
    if not is_right_type:
        return f"{rule.name}: expected {expected}, got{type(value).__name__}"
    if not math.isfinite(value):
        return f"{rule.name}: must be a finite number, got{value}"
    if rule.min_value is not None and value < rule.min_value:
        return f"{rule.name}:{value} is below the minimum {rule.min_value}"
    if rule.max_value is not None and value > rule.max_value:
        return f"{rule.name}:{value} is above the maximum {rule.max_value}"
    return None

def validate_record(raw:Any) -> list[str]:
    """Return the problems found in one raw coin (empty list= valid)"""
    if not isinstance(raw, dict):
        return  [f"record is not an object (got {type(raw).__name__})"]

    errors: list[str] = []
    for rule in COIN_RULES:
        value = raw.get(rule.name)

        if value is None:
            if rule.required:
                errors.append(f"{rule.name}: required field is missing or empty")
            continue

        error = _check_field(rule,value)
        if error:
            errors.append(error)

    high, low = raw.get("high_24h"), raw.get("low_24h")

    if _is_number(high) and _is_number(low) and high < low:
        errors.append(f"high_24h ({high}) is lower than low_24h ({low})")
    return errors

def validate_batch(raw_items: list[Any]) -> ValidationReport:
    """Validate every record and split them into valid and rejected."""
    report = ValidationReport()
    seen_ids : set[str] = set()

    for raw in raw_items:
        errors = validate_record(raw)

        if not errors :
            coin_id = raw["id"]
            if coin_id in seen_ids:
                errors.append(f"id: duplicate id{coin_id} in this batch")
            else:
                seen_ids.add(coin_id)
        if errors:
            rejected = RejectedRecord(raw=raw, errors=errors)
            report.rejected.append(rejected)
            logger.warning("Rejected coin '%s':%s",rejected.label,";".join(errors))
        else:
            report.valid.append(raw)
    logger.info(
        "Validation finished: %d valid, %d rejected",
        len(report.valid),len(report.rejected),
    )
    return report

def ensure_quality(
        report: ValidationReport,
        max_rejected_ratio: float= config.MAX_REJECTED_RATIO,
) -> None:
    """Stop the run if data is too broken to trust"""
    if report.total == 0:
        raise DataValidationError("The API returned no records")
    if not report.valid:
        raise DataValidationError("Every record failed validation")
    if report.rejected_ratio > max_rejected_ratio:
        raise DataValidationError(
            f"{report.rejected_ratio: .0%} of records were rejected"
            f"(limit: {max_rejected_ratio: .0%}). The API format may have changed"
        )