import pytest

from app.generator.utils import validate_url_scheme, is_safe_url_path


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://example.com/path?query=1",
        "https://example.com/some%20path/ok",
        "https://eletronicos.mercadolivre.com.br/seguranca-casa/#menu=categories",
        "https://www.mercadolivre.com.br/smart-cmera-wi-fi-positivo-casa-inteligente-com-carto-sd"
        "-32gb-branca/p/MLB27823553?pdp_filters=item_id:MLB4460338862#is_advertising=true"
        "&searchVariation=MLB27823553&backend_model=search-backend&position=1&search_layout=grid"
        "&type=pad&tracking_id=a2808f20-3ac8-403a-a7b6-21c50b2aa1b7&is_advertising=true&ad_domain"
        "=VQCATCORE_LST&ad_position=1&ad_click_id=N2Y0MDI0YTItOGQzMS00NDBlLWFhODYtOTY2NmQ1NzRmMDh1",
        "https://play.mercadolivre.com.br/#me.audience=api_loyalty_level_6_mlb&me.bu=3&me.bu_line"
        "=26&me.component_id=banner_menu_web_ml&me.content_id=BANNER_MENU_NIVEL_1A5_MELI_PLAY&me"
        ".flow=-1&me.logic=user_journey&me.position=0",
    ],
)
def test_validate_url_scheme_valid(url):
    assert validate_url_scheme(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com",
        "http:///no-domain",
        "javascript:alert(1)",
        "vbscript:malicious()",
    ],
)
def test_validate_url_scheme_with_invalid_base_scheme_or_domain_raises_value_error(url):
    with pytest.raises(ValueError) as exc_info:
        validate_url_scheme(url)
    assert "URL must start with http:// or https:// and include a valid domain" in str(
        exc_info.value
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/<script>",
        "http://example.com/</script>",
        "http://example.com/image.png?data:image/png;base64,abcd",
        "http://example.com/../etc/passwd",
        "http://example.com/page?id=1 OR 1=1",
        "http://example.com/run?cmd=whoami&&rm -rf /",
    ],
)
def test_validate_url_scheme_with_invalid_patterns_raises_value_error(url):
    with pytest.raises(ValueError) as exc_info:
        validate_url_scheme(url)
    assert "URL contains disallowed scheme or pattern" in str(exc_info.value)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/%3Cscript%3Ealert(1)%3C/script%3E",
        "http://example.com/img?data%3Aimage/png%3Bbase64%2Cabcd",
        "http://example.com/%2E%2E/%2E%2E/etc/passwd",
    ],
)
def test_validate_url_scheme_with_malicious_patterns_raises_value_error(url):
    with pytest.raises(ValueError) as exc_info:
        validate_url_scheme(url)
    assert "URL contains disallowed scheme or pattern" in str(exc_info.value)


@pytest.mark.parametrize(
    "path, expected",
    [
        ("abc123", True),
        ("ABCdef", True),
        ("a1B2c3", True),
        ("abc12", False),
        ("abcdefg", False),
        ("ab_cd1", False),
        ("abc$12", False),
        ("a bC12", False),
    ],
)
def test_is_safe_url_path(path, expected):
    assert is_safe_url_path(path) == expected
