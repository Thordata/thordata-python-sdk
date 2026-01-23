from thordata.tools import Amazon


def test_amazon_product_tool():
    tool = Amazon.Product(asin="B08XYZ", domain="amazon.co.uk")

    assert tool.get_spider_id() == "amazon_product_by-asin"
    assert tool.get_spider_name() == "amazon.com"

    params = tool.to_task_parameters()
    assert params["asin"] == "B08XYZ"
    assert params["domain"] == "amazon.co.uk"


def test_tool_integration_with_config():
    # Verify it works with the Config model logic
    tool = Amazon.Search(keyword="laptop", min_price=100.5)
    params = tool.to_task_parameters()

    assert params["keyword"] == "laptop"
    assert params["min_price"] == 100.5
    assert "max_price" not in params  # Should allow None
