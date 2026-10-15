from cortex_brand_analysis.mcp.server import mcp


def test_native_mcp_server_is_created():
    assert mcp.name == "Cortex Brand Analysis"
