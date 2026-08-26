import json
from datetime import date
from decimal import Decimal

from ingestion.json_ingestion import load_json


def valid_record(transaction_id=1):
    return {
        "id": transaction_id,
        "date": "1420-01-03",
        "branch": "Florence",
        "type": "operating_expense",
        "counterparty": "Parchment Vendor",
        "description": "Writing materials",
        "debit_account": "Supplies",
        "debit_amount": "400.00",
        "credit_account": "Cash",
        "credit_amount": "400.00",
        "credit_account_2": "",
        "credit_amount_2": "",
        "currency": "florin",
    }


def write_json(tmp_path, payload):
    path = tmp_path / "transactions.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def accept_all(record):
    return True, []


def test_load_json_normalizes_valid_record(tmp_path):
    result = load_json(write_json(tmp_path, [valid_record()]), accept_all)

    assert result.total_records == 1
    assert result.accepted_count == 1
    assert result.rejected_count == 0
    assert result.source_errors == []
    assert result.accepted[0]["id"] == 1
    assert result.accepted[0]["date"] == date(1420, 1, 3)
    assert result.accepted[0]["debit_amount"] == Decimal("400.00")
    assert result.accepted[0]["credit_amount"] == Decimal("400.00")
    assert result.accepted[0]["credit_account_2"] is None
    assert result.accepted[0]["credit_amount_2"] is None


def test_malformed_json_returns_source_error(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('[{"id": 1}', encoding="utf-8")

    result = load_json(path, accept_all)

    assert result.accepted_count == 0
    assert result.rejected_count == 0
    assert "Malformed JSON" in result.source_errors[0]


def test_json_root_must_be_a_list(tmp_path):
    result = load_json(write_json(tmp_path, valid_record()), accept_all)

    assert result.total_records == 0
    assert result.source_errors == ["JSON root must be a list of transaction objects"]


def test_malformed_record_does_not_stop_batch(tmp_path):
    malformed = valid_record(1)
    malformed["debit_amount"] = "not-a-number"
    payload = [malformed, valid_record(2)]

    result = load_json(write_json(tmp_path, payload), accept_all)

    assert result.total_records == 2
    assert result.accepted_count == 1
    assert result.accepted[0]["id"] == 2
    assert result.rejected_count == 1
    assert result.rejected[0].record_number == 1
    assert result.rejected[0].reasons == ("debit_amount must be numeric",)


def test_missing_required_normalization_field_is_rejected(tmp_path):
    missing_date = valid_record()
    del missing_date["date"]

    result = load_json(write_json(tmp_path, [missing_date]), accept_all)

    assert result.accepted_count == 0
    assert result.rejected_count == 1
    assert result.rejected[0].reasons == ("missing required field: date",)


def test_non_object_record_is_rejected(tmp_path):
    result = load_json(write_json(tmp_path, ["not an object"]), accept_all)

    assert result.rejected_count == 1
    assert result.rejected[0].reasons == ("transaction must be a JSON object",)


def test_shared_validator_rejection_is_reported(tmp_path):
    def reject_unbalanced(record):
        return False, ["debit and credit totals do not match"]

    result = load_json(
        write_json(tmp_path, [valid_record()]),
        reject_unbalanced,
    )

    assert result.accepted_count == 0
    assert result.rejected_count == 1
    assert result.rejected[0].reasons == (
        "debit and credit totals do not match",
    )


def test_incremental_loading_only_validates_newer_records(tmp_path):
    validated_ids = []

    def tracking_validator(record):
        validated_ids.append(record["id"])
        return True, []

    payload = [valid_record(1), valid_record(2), valid_record(3)]
    result = load_json(
        write_json(tmp_path, payload),
        tracking_validator,
        last_processed_id=2,
    )

    assert validated_ids == [3]
    assert result.accepted_count == 1
    assert result.skipped_by_incremental_filter == 2


def test_missing_file_returns_source_error(tmp_path):
    result = load_json(tmp_path / "missing.json", accept_all)

    assert result.accepted_count == 0
    assert result.source_errors == [f"JSON file not found: {tmp_path / 'missing.json'}"]
