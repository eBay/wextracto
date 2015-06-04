#! /usr/bin/env python -u
# -*- coding: cp1252 -*-
# <PythonProxy.py>
#
#Copyright (c) <2009> <Fábio Domingues - fnds3000 in gmail.com>
#
#Permission is hereby granted, free of charge, to any person
#obtaining a copy of this software and associated documentation
#files (the "Software"), to deal in the Software without
#restriction, including without limitation the rights to use,
#copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the
#Software is furnished to do so, subject to the following
#conditions:
#
#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.

"""\
Copyright (c) <2009> <Fábio Domingues - fnds3000 in gmail.com> <MIT Licence>

                  **************************************
                 *** Python Proxy - A Fast HTTP proxy ***
                  **************************************

Neste momento este proxy é um Elie Proxy.

Suporta os métodos HTTP:
 - OPTIONS;
 - GET;
 - HEAD;
 - POST;
 - PUT;
 - DELETE;
 - TRACE;
 - CONENCT.

Suporta:
 - Conexões dos cliente em IPv4 ou IPv6;
 - Conexões ao alvo em IPv4 e IPv6;
 - Conexões todo o tipo de transmissão de dados TCP (CONNECT tunneling),
     p.e. ligações SSL, como é o caso do HTTPS.

A fazer:
 - Verificar se o input vindo do cliente está correcto;
   - Enviar os devidos HTTP erros se não, ou simplesmente quebrar a ligação;
 - Criar um gestor de erros;
 - Criar ficheiro log de erros;
 - Colocar excepções nos sítios onde é previsível a ocorrência de erros,
     p.e.sockets e ficheiros;
 - Rever tudo e melhorar a estrutura do programar e colocar nomes adequados nas
     variáveis e métodos;
 - Comentar o programa decentemente;
 - Doc Strings.

Funcionalidades futuras:
 - Adiconar a funcionalidade de proxy anónimo e transparente;
 - Suportar FTP?.


(!) Atenção o que se segue só tem efeito em conexões não CONNECT, para estas o
 proxy é sempre Elite.

Qual a diferença entre um proxy Elite, Anónimo e Transparente?
 - Um proxy elite é totalmente anónimo, o servidor que o recebe não consegue ter
     conhecimento da existência do proxy e não recebe o endereço IP do cliente;
 - Quando é usado um proxy anónimo o servidor sabe que o cliente está a usar um
     proxy mas não sabe o endereço IP do cliente;
     É enviado o cabeçalho HTTP "Proxy-agent".
 - Um proxy transparente fornece ao servidor o IP do cliente e um informação que
     se está a usar um proxy.
     São enviados os cabeçalhos HTTP "Proxy-agent" e "HTTP_X_FORWARDED_FOR".

"""

from __future__ import print_function
import os
import signal
import sys
import socket, select, re
import threading
from subprocess import Popen, PIPE
from six import PY3, binary_type

__version__ = b'0.1.0 Draft 1'
BUFLEN = 8192
VERSION = b'Python Proxy/'+__version__
HTTPVER = b'HTTP/1.1'

HTTP_METHODS = [
    b'DELETE',
    b'GET',
    b'HEAD',
    b'OPTIONS',
    b'PATCH',
    b'POST',
    b'PUT',
    b'TRACE',
]

pat = b'^((' + b'|'.join(HTTP_METHODS) + b')\s+.*)$'
request_lines = re.compile(pat, re.M | re.I)

CRLF = b'\r\n'
NL = b'\n'

CONNECT = b'CONNECT'

class ConnectionHandler:
    def __init__(self, connection, address, timeout):
        if PY3:
            self.stdout = sys.stdout.buffer
        else:
            self.stdout = sys.stdout
        self.client = connection
        self.client_buffer = b''
        self.timeout = timeout
        self.method, self.path, self.protocol = self.get_base_header()
        if self.method==b'CONNECT':
            self.method_CONNECT()
        elif self.method in HTTP_METHODS:
            self.method_others()
        self.client.close()
        self.target.close()

    def get_base_header(self):
        while 1:
            self.client_buffer += self.client.recv(BUFLEN)
            end = self.client_buffer.find(NL)
            if end!=-1:
                break
        self.stdout.write(self.client_buffer[:end] + NL)
        data = (self.client_buffer[:end+1]).split()
        self.client_buffer = self.client_buffer[end+1:]
        return data

    def method_CONNECT(self):
        self._connect_target(self.path)
        self.client.send(HTTPVER+b' 200 Connection established\n'+
                         b'Proxy-agent: %s\n\n'%VERSION)
        self.client_buffer = b''
        self._read_write()

    def method_others(self):
        self.path = self.path[7:]
        i = self.path.find(b'/')
        host = self.path[:i]
        path = self.path[i:]
        self._connect_target(host)
        request = b' '.join([self.method, path, self.protocol]) + CRLF
        self.target.send(request + self.client_buffer)
        self.client_buffer = b''
        self._read_write()

    def _connect_target(self, host):
        i = host.find(b':')
        if i!=-1:
            port = int(host[i+1:])
            host = host[:i]
        else:
            port = 80
        (soc_family, _, _, _, address) = socket.getaddrinfo(host, port)[0]
        self.target = socket.socket(soc_family)
        self.target.connect(address)

    def _read_write(self):
        time_out_max = self.timeout/3
        socs = [self.client, self.target]
        count = 0
        while 1:
            count += 1
            (recv, _, error) = select.select(socs, [], socs, 3)
            if error:
                break
            if recv:
                for in_ in recv:
                    data = in_.recv(BUFLEN)
                    if in_ is self.client:
                        for match in request_lines.finditer(data):
                            self.stdout.write(match.group(1) + NL)
                        out = self.target
                    else:
                        out = self.client
                    if data:
                        out.send(data)
                        count = 0
            if count == time_out_max:
                break

def start_server(host='localhost', port=None, IPv6=False, timeout=60,
                  handler=ConnectionHandler):
    if IPv6==True:
        soc_type=socket.AF_INET6
    else:
        soc_type=socket.AF_INET
    soc = socket.socket(soc_type)
    if port is None:
        port = int(os.environ.get('TESTS_HTTPPROXY_PORT', 0))
    soc.bind((host, port))
    print("http://%s:%d" % soc.getsockname())
    # we really need this to be seen immediately
    sys.stdout.flush()
    soc.listen(0)
    while 1:
        try:
            accepted = soc.accept()
        except KeyboardInterrupt:
            break

        args = accepted + (timeout,)
        thread = threading.Thread(target=handler, args=args)
        thread.start()



class HttpProxy(object):

    def __enter__(self):
        self.popen = Popen(['python', __file__], stdout=PIPE, env=os.environ)
        self.url = self.popen.stdout.readline().rstrip()
        if isinstance(self.url, binary_type):
            self.url = self.url.decode('utf-8')
        # a requests styel proxies dictionary
        self.proxies = {'http': self.url, 'https': self.url}
        return self

    def __exit__(self, *exc_info):
        os.kill(self.popen.pid, signal.SIGINT)
        self.requests = [r.strip() for r in self.popen.stdout.readlines()]



if __name__ == '__main__':
    start_server()
