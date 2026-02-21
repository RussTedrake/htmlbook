from htmlbook.install_html_meta_data import install_html_meta_data


def test_install_html_meta_data_check() -> None:
    assert not install_html_meta_data(check=True)
