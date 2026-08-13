from paymentcopilot.graph.classify import classify_query


def test_txn_id_routes_to_uc2():
    route, reason = classify_query("Why did txn_88213 fail?")
    assert route == "uc2_transaction"
    assert "txn_88213" in reason


def test_policy_phrasing_routes_to_uc3():
    route, _ = classify_query("Can I refund this transaction after 90 days?")
    assert route == "uc3_policy"


def test_docs_question_routes_to_uc1():
    route, _ = classify_query("How do I verify a webhook signature?")
    assert route == "uc1_docs"


def test_api_refund_howto_routes_to_uc1_not_uc3():
    route, _ = classify_query("How do I issue a refund through the API?")
    assert route == "uc1_docs"


def test_unrelated_question_routes_to_out_of_scope():
    route, _ = classify_query("What's the weather like today?")
    assert route == "out_of_scope"
