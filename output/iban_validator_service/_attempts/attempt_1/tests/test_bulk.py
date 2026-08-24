import pytest
from src import country_registry
from src.models import MAX_BULK_ITEMS


@pytest.fixture(autouse=True)
def _reset_registry():
    country_registry.reset_state()
    yield
    country_registry.reset_state()


def test_bulk_mixed_list_returns_200_and_per_item_results(client):
    payload = {
        "ibans": [
            "NL91ABNA0417164300",
            "DE89 3704 0044 0532 0130 00",
            "NL91ABNA0417164301",
            "XX00INVALID",
            "FR761234",
        ],
        "style": "print",
        "fail_fast": False,
    }
    response = client.post("/validate/bulk", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 5
    assert len(body["results"]) == 5
    assert [r["index"] for r in body["results"]] == [0, 1, 2, 3, 4]

    assert body["results"][0]["status"] == "valid"
    assert body["results"][0]["formatted"] == "NL91 ABNA 0417 1643 00"
    assert body["results"][0]["compact"] == "NL91ABNA0417164300"
    assert body["results"][0]["errors"] == []

    assert body["results"][1]["status"] == "valid"
    assert body["results"][1]["compact"] == "DE89370400440532013000"
    assert body["results"][1]["formatted"] == "DE89 3704 0044 0532 0130 00"
    assert body["results"][1]["length"] == 22
    assert body["results"][1]["expected_length"] == 22

    assert body["results"][2]["status"] == "invalid"
    assert [e["code"] for e in body["results"][2]["errors"]] == ["CHECKSUM_FAILED"]

    assert body["results"][3]["status"] == "invalid"
    assert body["results"][3]["country_code"] == "XX"
    assert body["results"][3]["expected_length"] is None
    assert [e["code"] for e in body["results"][3]["errors"]] == ["UNKNOWN_COUNTRY"]

    assert body["results"][4]["status"] == "invalid"
    assert body["results"][4]["expected_length"] == 27
    assert [e["code"] for e in body["results"][4]["errors"]] == ["INVALID_LENGTH"]


def test_bulk_preserves_order_and_indices(client):
    payload = {
        "ibans": ["BE68539007547034", "XX00INVALID", "NL91ABNA0417164300"]
    }
    response = client.post("/validate/bulk", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert [r["index"] for r in body["results"]] == [0, 1, 2]
    assert [r["input"] for r in body["results"]] == [
        "BE68539007547034",
        "XX00INVALID",
        "NL91ABNA0417164300",
    ]
    assert [r["status"] for r in body["results"]] == ["valid", "invalid", "valid"]


def test_bulk_summary_counts_mixed_list(client):
    payload = {
        "ibans": [
            "NL91ABNA0417164300",
            "DE89370400440532013000",
            "NL91ABNA0417164301",
            "XX00INVALID",
            12345,
        ]
    }
    response = client.post("/validate/bulk", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 5
    assert body["summary"]["valid"] == 2
    assert body["summary"]["invalid"] == 2
    assert body["summary"]["errors"] == 1
    assert body["summary"]["stopped_early"] is False


def test_bulk_handles_none_empty_and_non_string_items(client):
    payload = {
        "ibans": [None, "", 42, {"iban": "NL91ABNA0417164300"}, ["NL91ABNA0417164300"]]
    }
    response = client.post("/validate/bulk", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 5
    for r in body["results"]:
        assert r["status"] in ("invalid", "error")
        assert r["valid"] is False
        assert len(r["errors"]) >= 1
    assert [e["code"] for e in body["results"][0]["errors"]] == ["NOT_A_STRING"]
    assert [e["code"] for e in body["results"][1]["errors"]] == ["EMPTY_INPUT"]
    assert [e["code"] for e in body["results"][2]["errors"]] == ["NOT_A_STRING"]
    assert body["summary"]["errors"] == 4
    assert body["summary"]["invalid"] == 1
    assert body["summary"]["valid"] == 0


def test_bulk_empty_list(client):
    payload = {"ibans": []}
    response = client.post("/validate/bulk", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["results"] == []
    assert body["summary"] == {"valid": 0, "invalid": 0, "errors": 0, "stopped_early": False}


def test_bulk_above_max_batch_size_returns_422(client):
    payload = {"ibans": ["NL91ABNA0417164300"] * (MAX_BULK_ITEMS + 1)}
    response = client.post("/validate/bulk", json=payload)
    assert response.status_code == 422


def test_bulk_fail_fast_stops_after_first_non_valid_item(client):
    payload = {
        "ibans": ["NL91ABNA0417164300", "NL91ABNA0417164301", "DE89370400440532013000"],
        "fail_fast": True,
    }
    response = client.post("/validate/bulk", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert len(body["results"]) == 2
    assert [r["index"] for r in body["results"]] == [0, 1]
    assert body["summary"]["valid"] == 1
    assert body["summary"]["invalid"] == 1
    assert body["summary"]["errors"] == 0
    assert body["summary"]["stopped_early"] is True


def test_bulk_style_compact_applies_to_formatted(client):
    payload = {"ibans": ["nl91 abna 0417 1643 00"], "style": "compact"}
    response = client.post("/validate/bulk", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["formatted"] == "NL91ABNA0417164300"
    assert body["results"][0]["compact"] == "NL91ABNA0417164300"
    assert body["results"][0]["status"] == "valid"
