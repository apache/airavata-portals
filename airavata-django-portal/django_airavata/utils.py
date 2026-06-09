import logging
import ssl
import queue
from django.conf import settings
from contextlib import contextmanager

import thrift_connector.connection_pool as connection_pool
from airavata.api import Airavata
from thrift.protocol import TBinaryProtocol
from thrift.protocol.TMultiplexedProtocol import TMultiplexedProtocol
from thrift.transport import TSocket, TSSLSocket, TTransport

log = logging.getLogger(__name__)


class ThriftConnectionException(Exception):
    pass


class ThriftClientException(Exception):
    pass


def get_unsecure_transport(hostname, port):
    # Create a socket to the Airavata Server
    transport = TSocket.TSocket(hostname, port)

    # Use Buffered Protocol to speedup over raw sockets
    transport = TTransport.TBufferedTransport(transport)
    return transport


def get_secure_transport(hostname, port):

    # Create a socket to the Airavata Server
    transport = TSSLSocket.TSSLSocket(
        hostname,
        port,
        cert_reqs=ssl.CERT_REQUIRED,
        ca_certs=settings.CA_CERTS_PATH,
    )
    return TTransport.TBufferedTransport(transport)


def get_transport(hostname, port, secure=True):
    if secure:
        transport = get_secure_transport(hostname, port)
    else:
        transport = get_unsecure_transport(hostname, port)
    return transport


def create_airavata_client(transport):

    # Airavata currently uses Binary Protocol
    protocol = TBinaryProtocol.TBinaryProtocol(transport)

    # Create a Airavata client to use the protocol encoder
    client = Airavata.Client(protocol)
    return client


def get_binary_protocol(transport):
    return TBinaryProtocol.TBinaryProtocol(transport)


def get_airavata_client():
    """Get Airavata API client as context manager (use in `with statement`)."""
    return get_thrift_client(settings.AIRAVATA_API_HOST,
                             settings.AIRAVATA_API_PORT,
                             settings.AIRAVATA_API_SECURE,
                             create_airavata_client)


@contextmanager
def get_thrift_client(host, port, is_secure, client_generator):
    transport = get_transport(host, port, is_secure)
    client = client_generator(transport)

    try:
        transport.open()
        log.debug("Thrift connection opened to {}:{}, "
                  "secure={}".format(host, port, is_secure))
        try:
            yield client
        except Exception as e:
            log.exception("Thrift client error occurred")
            raise ThriftClientException(
                "Thrift client error occurred: " + str(e)) from e
        finally:
            if transport.isOpen():
                transport.close()
                log.debug("Thrift connection closed to {}:{}, "
                          "secure={}".format(host, port, is_secure))
    except ThriftClientException as tce:
        # Allow thrift client errors to bubble up
        raise tce
    except Exception as e:
        msg = "Failed to open thrift connection to {}:{}, secure={}".format(
            host, port, is_secure)
        log.debug(msg)
        raise ThriftConnectionException(msg) from e


@contextmanager
def simple_thrift_connection(pool):
    """Context manager for borrowing a connection from the pool."""
    conn = pool.get_connection()
    try:
        yield conn['client']
    finally:
        pool.return_connection(conn)


class SimpleThriftPool:
    """
    A thread-safe Thrift connection pool that uses raw Thrift and the TBufferedTransport.
    """

    def __init__(self, service, host, port, size=5, secure=False, ca_certs=None):
        self._service = service
        self._host = host
        self._port = port
        self._size = size
        self._secure = secure
        self._ca_certs = ca_certs or settings.CA_CERTS_PATH
        self._pool = queue.Queue(maxsize=size)
        self._initialize_pool()

    def _initialize_pool(self):
        for _ in range(self._size):
            self._pool.put(self._create_connection())

    def _create_connection(self):
        if self._secure:
            socket = TSSLSocket.TSSLSocket(
                host=self._host,
                port=self._port,
                cert_reqs=ssl.CERT_REQUIRED,
                ca_certs=self._ca_certs,
            )
        else:
            socket = TSocket.TSocket(host=self._host, port=self._port)
        transport = TTransport.TBufferedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = self._service.Client(protocol)
        transport.open()
        return {'client': client, 'transport': transport}

    def get_connection(self):
        conn = self._pool.get()
        if not self._is_alive(conn):
            log.debug("Stale connection detected, creating new one")
            try:
                conn['transport'].close()
            except Exception:
                pass
            conn = self._create_connection()
        return conn

    def _is_alive(self, conn):
        try:
            if not conn['transport'].isOpen():
                return False
            conn['client'].getAPIVersion()
            return True
        except Exception:
            return False

    def return_connection(self, conn):
        try:
            if conn['transport'].isOpen():
                conn['transport'].close()
        except Exception:
            pass
        self._pool.put(self._create_connection())

    def connection(self):
        return simple_thrift_connection(self)


class CustomThriftClient(connection_pool.ThriftClient):
    secure = False
    validate = False

    @classmethod
    def get_socket_factory(cls):
        if not cls.secure:
            return super().get_socket_factory()
        else:
            def factory(host, port):
                return TSSLSocket.TSSLSocket(
                    host,
                    port,
                    cert_reqs=ssl.CERT_REQUIRED,
                    ca_certs=settings.CA_CERTS_PATH,
                )

            return factory

    def ping(self):
        try:
            self.client.getAPIVersion()
        except Exception as e:
            log.debug("getAPIVersion failed: {}".format(str(e)))
            raise


class MultiplexThriftClientMixin:
    service_name = None

    @classmethod
    def get_protoco_factory(cls):
        def factory(transport):
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            multiplex_prot = TMultiplexedProtocol(protocol, cls.service_name)
            return multiplex_prot
        return factory


class AiravataAPIThriftClient(CustomThriftClient):
    secure = settings.AIRAVATA_API_SECURE


airavata_api_client_pool = SimpleThriftPool(
    Airavata,
    settings.AIRAVATA_API_HOST,
    settings.AIRAVATA_API_PORT,
    secure=settings.AIRAVATA_API_SECURE,
    ca_certs=settings.CA_CERTS_PATH,
)
