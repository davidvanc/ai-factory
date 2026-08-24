import pytest
from src.iban_registry import reset_state
from src.logic import MAX_BULK_ITEMS


@pytest.fixture(autouse=True)
def _reset():
    reset_state()
    yield
    reset_state()


def test_bulk_mixed_items_all_processed(client, auth_headers):
    response = client.post(
        "/validate/bulk",
        json={
            "ibans": [
                "NL91ABNA0417164300",
                "DE89 3704 0044 0532 0130 00",
                "GB82WEST12345698765432",
                "NL91ABNA0417164301",
                "XX00INVALID",
                "",
            ],
            "format_output": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 6
    assert [r["status"] for r in body["results"]] == [
        "valid",
        "valid",
        "valid",
        "invalid",
        "invalid",
        "invalid",
    ]
    assert body["results"][3]["errors"][0]["code"] == "CHECKSUM_FAILED"
    assert body["results"][4]["errors"][0]["code"] == "COUNTRY_NOT_SUPPORTED"
    assert body["results"][5]["errors"][0]["code"] == "EMPTY_INPUT"
    assert body["results"][1]["iban"] == "DE89370400440532013000"
    assert body["results"][1]["formatted"] == "DE89 3704 0044 0532 0130 00"


def test_bulk_preserves_index_and_order(client, auth_headers):
    response = client.post(
        "/validate/bulk",
        json={
            "ibans": [
                "NL91ABNA0417164300",
                "XX00INVALID",
                "DE89370400440532013000",
            ]
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert [r["index"] for r in results] == [0, 1, 2]
    assert [r["country_code"] for r in results] == ["NL", "XX", "DE"]
    assert [r["input"] for r in results] == [
        "NL91ABNA0417164300",
        "XX00INVALID",
        "DE89370400440532013000",
    ]


def test_bulk_summary_totals(client, auth_headers):
    response = client.post(
        "/validate/bulk",
        json={
            "ibans": [
                "NL91ABNA0417164300",
                "DE89 3704 0044 0532 0130 00",
                "GB82WEST12345698765432",
                "NL91ABNA0417164301",
                "XX00INVALID",
                "",
            ],
            "format_output": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary == {"total": 6, "valid": 3, "invalid": 3, "errors": 0}
    assert summary["total"] == summary["valid"] + summary["invalid"] + summary["errors"]


def test_bulk_non_string_items_marked_error(client, auth_headers):
    response = client.post(
        "/validate/bulk",
        json={"ibans": ["NL91ABNA0417164300", None, 12345]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    results = body["results"]
    assert results[1]["status"] == "error"
    assert results[2]["status"] == "error"
    assert results[1]["valid"] is False
    assert results[1]["input"] is None
    assert results[1]["iban"] is None
    assert results[1]["errors"][0]["code"] == "NOT_A_STRING"
    assert body["summary"] == {"total": 3, "valid": 1, "invalid": 0, "errors": 2}


def test_bulk_empty_list(client, auth_headers):
    response = client.post(
        "/validate/bulk", json={"ibans": []}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"] == []
    assert body["summary"] == {"total": 0, "valid": 0, "invalid": 0, "errors": 0}


def test_bulk_over_limit_returns_422(client, auth_headers):
    response = client.post(
        "/validate/bulk",
        json={"ibans": ["NL91ABNA0417164300"] * (MAX_BULK_ITEMS + 1)},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_bulk_format_output_false_omits_formatted(client, auth_headers):
    response = client.post(
        "/validate/bulk",
        json={"ibans": ["NL91ABNA0417164300"], "format_output": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["formatted"] is None
    assert result["iban"] == "NL91ABNA0417164300"
    assert result["status"] == "valid"
