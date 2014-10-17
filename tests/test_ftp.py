from wex.url import URL

expected_lines = [
    b"FTP/1.0 200 OK\r\n",
    b"X-wex-url: ftp://anonymous:me@ftp.kernel.org/pub/site/README\r\n",
    b"\r\n",
    b"This directory contains files related to the operation of the\n",
]
expected_content = b''.join(expected_lines)

url = 'ftp://anonymous:me@ftp.kernel.org/pub/site/README'


def test_ftp_read():
    readables = list(URL(url).get())
    assert len(readables) == 1
    r0 = readables[0]
    chunk = r0.read(2**16)
    content = chunk
    chunk = r0.read(2**16)
    assert not chunk
    assert content.startswith(expected_content)


def test_ftp_readline():
    readables = list(URL(url).get())
    assert len(readables) == 1
    r0 = readables[0]
    first_four_lines = [r0.readline() for i in range(4)]
    assert first_four_lines == expected_lines[:4]
