from cortex_brand_analysis.domain.model_policy import ModelPolicy


class FakeSettings:
    openai_conversation_model = "conversation-test"
    openai_analytical_model = "analysis-test"


def test_model_policy_routes_roles():
    policy = ModelPolicy.from_settings(FakeSettings())
    assert policy.for_role("conversation").model == "conversation-test"
    assert policy.for_role("planning").model == "analysis-test"
    assert policy.for_role("interpretation").reasoning_effort == "high"
    assert policy.for_role("evaluation").model == "analysis-test"
