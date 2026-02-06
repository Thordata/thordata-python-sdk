"""
Tests for the internal tools registry module.

Focuses on caching behavior and tool discovery.
"""

from thordata._tools_registry import (
    _clear_cache,
    get_tool_class_by_key,
    get_tool_info,
    list_tools_metadata,
    resolve_tool_key,
)


def test_list_tools_metadata_returns_data():
    """Verify that list_tools_metadata returns tool data."""
    tools, group_counts = list_tools_metadata()

    assert isinstance(tools, list)
    assert len(tools) > 0
    assert isinstance(group_counts, dict)

    # Verify structure
    for tool in tools:
        assert "key" in tool
        assert "group" in tool
        assert "spider_id" in tool or "class_name" in tool
        assert "fields" in tool


def test_list_tools_metadata_with_group_filter():
    """Verify group filtering works."""
    tools, group_counts = list_tools_metadata(group="ecommerce")

    # All tools should be in ecommerce group
    for tool in tools:
        assert tool["group"] == "ecommerce" or tool["group"] == "default"


def test_list_tools_metadata_with_keyword():
    """Verify keyword search works."""
    tools, group_counts = list_tools_metadata(keyword="amazon")

    # At least one tool should match "amazon"
    assert len(tools) > 0

    # Verify search haystack includes key, spider_id, spider_name
    for tool in tools:
        haystack = f"{tool['key']} {tool.get('spider_id', '')} {tool.get('spider_name', '')}"
        assert "amazon" in haystack.lower()


def test_resolve_tool_key_canonical():
    """Test resolving canonical tool keys."""
    # This should resolve to a valid tool
    result = resolve_tool_key("ecommerce.amazon_product_by-url")
    assert "." in result
    assert "amazon" in result.lower()


def test_resolve_tool_key_raw_spider_id():
    """Test resolving raw spider IDs."""
    # Try to resolve a common tool by spider_id
    result = resolve_tool_key("amazon_product_by-url")
    assert "." in result
    assert "amazon" in result.lower()


def test_resolve_tool_key_empty():
    """Test that empty key raises KeyError."""
    try:
        resolve_tool_key("")
        assert False, "Should have raised KeyError"
    except KeyError as e:
        assert "empty" in str(e).lower()


def test_resolve_tool_key_unknown():
    """Test that unknown key raises KeyError."""
    try:
        resolve_tool_key("not.a.real.tool.key")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass


def test_get_tool_class_by_key():
    """Test getting tool class by key."""
    cls = get_tool_class_by_key("ecommerce.amazon_product_by-url")
    assert cls is not None
    assert hasattr(cls, "get_spider_id")
    assert hasattr(cls, "get_spider_name")
    assert hasattr(cls, "to_task_parameters")


def test_get_tool_class_by_key_invalid():
    """Test that invalid key raises KeyError."""
    try:
        get_tool_class_by_key("not.a.real.tool.key")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass


def test_get_tool_info():
    """Test getting tool metadata."""
    info = get_tool_info("ecommerce.amazon_product_by-url")

    assert "key" in info
    assert "group" in info
    assert "spider_id" in info
    assert "fields" in info
    assert isinstance(info["fields"], list)


def test_caching_behavior():
    """Test that caching improves performance."""
    # Clear cache first
    _clear_cache()

    # First call - should build cache
    tools1, _ = list_tools_metadata()

    # Second call - should use cache
    tools2, _ = list_tools_metadata()

    # Results should be identical
    assert len(tools1) == len(tools2)

    # Keys should match
    keys1 = {t["key"] for t in tools1}
    keys2 = {t["key"] for t in tools2}
    assert keys1 == keys2


def test_clear_cache():
    """Test that _clear_cache works."""
    # Build cache by calling a function
    list_tools_metadata()

    # Clear cache
    _clear_cache()

    # Should work without issues
    tools, _ = list_tools_metadata()
    assert len(tools) > 0


def test_get_tool_class_by_key_caching():
    """Test that get_tool_class_by_key uses cache."""
    # Clear cache first
    _clear_cache()

    # First call - should build cache
    cls1 = get_tool_class_by_key("ecommerce.amazon_product_by-url")

    # Second call - should use cache
    cls2 = get_tool_class_by_key("ecommerce.amazon_product_by-url")

    # Should return same class instance
    assert cls1 is cls2


def test_list_tools_metadata_caching():
    """Test that list_tools_metadata uses cache."""
    # Clear cache first
    _clear_cache()

    # First call - should build cache
    tools1, counts1 = list_tools_metadata()

    # Second call - should use cache
    tools2, counts2 = list_tools_metadata()

    # Results should be exactly the same objects
    assert tools1 is tools2
    assert counts1 is counts2


def test_tool_schema_video_flag():
    """Test that video tools have correct flag."""
    from thordata._tools_registry import _tool_schema

    tools, _ = list_tools_metadata()

    # Check that at least some tools have video flag set correctly
    for tool in tools:
        assert "video" in tool
        assert isinstance(tool["video"], bool)


def test_tool_schema_field_types():
    """Test that tool schema includes field types."""
    from thordata._tools_registry import _tool_schema

    cls = get_tool_class_by_key("ecommerce.amazon_product_by-url")
    schema = _tool_schema(cls)

    assert "fields" in schema
    assert isinstance(schema["fields"], list)

    for field in schema["fields"]:
        assert "name" in field
        assert "type" in field
        assert "default" in field


def test_group_counts():
    """Test that group counts are accurate."""
    tools, group_counts = list_tools_metadata()

    # Count tools per group
    actual_counts = {}
    for tool in tools:
        group = tool["group"] or "default"
        actual_counts[group] = actual_counts.get(group, 0) + 1

    # Verify counts match
    assert group_counts == actual_counts
