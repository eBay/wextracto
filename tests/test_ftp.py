from wex.url import URL

url = 'ftp://anonymous:me@speedtest.tele2.net/1KB.zip'

expected_lines = [
    b"FTP/1.0 200 OK\r\n",
    b"X-wex-url: " + url.encode('utf-8') + b"\r\n",
    b"\r\n",
]
expected_content = b''.join(expected_lines)


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
    n = 3
    r0 = readables[0]
    first_few_lines = [r0.readline() for i in range(n)]
    assert first_few_lines == expected_lines[:n]
