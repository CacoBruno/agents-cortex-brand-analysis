from cortex_brand_analysis.workflows.compatibility import CompatibilityWorkflow


def test_compatibility_registry_lists_source_project_capabilities():
    capabilities = CompatibilityWorkflow().capabilities().capabilities
    names = {(item.group, item.tool_name) for item in capabilities}

    assert ("measurements", "sentiment_classification") in names
    assert ("context", "build_coverage_summary") in names
    assert ("pattern", "build_daily_pattern_dict") in names
    assert ("visualization", "generate_chart") in names
    assert ("highlights", "generate_highlights_tool") in names


def test_native_indexes_are_marked_as_native():
    capabilities = CompatibilityWorkflow().capabilities().capabilities
    nps = next(
        item
        for item in capabilities
        if item.group == "index" and item.tool_name == "calc_nps_score"
    )
    assert nps.migrated_native is True
