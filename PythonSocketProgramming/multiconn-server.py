#!/usr/bin/env python3

import sys
import socket
import selectors
import types
import ipaddress
import os
import signal



sel = selectors.DefaultSelector()

def exit_program( signal, frame ):
    sel.close()
    sys.exit( 0 )


def accept_wrapper( sock ):
    conn, addr = sock.accept()
    print( 'accepted connection from', addr )
    conn.setblocking( False )
    #conn.setblocking( True )
    data = types.SimpleNamespace( addr=addr, inb=b'', outb=b'' )
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register( conn, events, data=data )


def service_connection( key, mask ):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv( 1024 )
        if recv_data:
            data.outb += recv_data
        else:
            print( 'closing connection to', data.addr )
            sel.unregister( sock )
            sock.close()

    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print( 'echoing', repr( data.outb ), 'to', data.addr )
            sent = sock.send( data.outb )
            data.outb = data.outb[sent:]

if len( sys.argv ) != 3:
    print( 'usage:', sys.argv[0], '<host> <port>' )
    sys.exit( 1 )

#signal.signal( signal.SIGINT, exit_program )


host = sys.argv[1].replace("'", "") # This allows you to pass the quad as a string, '127.0.0.1'
host = host.replace('"', '' ) # To handle double quotes
port = int(sys.argv[2])
lsock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
lsock.bind( ( host, port ) )



try:
    lsock.listen()
    print( 'listening on', (host, port) )
    lsock.setblocking( False )
    sel.register( lsock, selectors.EVENT_READ, data=None )
    while True:
        events = sel.select( timeout=None )
        for key, mask in events:
            if key.data is None:
                accept_wrapper( key.fileobj )
            else:
                service_connection( key, mask )
except KeyboardInterrupt:
    print( 'caught keyboard interrupt, exiting...' )
finally:
    sel.close()