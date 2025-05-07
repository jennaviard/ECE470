import socket
from shmessage import shmessage


class shpdu:
   def __init__(self, comm: socket.socket):
       self._sock = comm


   def _loopRecv(self, size: int):
       data = bytearray(size)
       mv = memoryview(data)
       while size > 0:
           rsize = self._sock.recv_into(mv, size)
           if rsize == 0:
               raise ConnectionResetError()
           mv = mv[rsize:]
           size -= rsize
       return data


   def sendMessage(self, mess: shmessage):
       mdata = mess.marshal().encode('utf-8')
       size = len(mdata)
       self._sock.sendall(size.to_bytes(4, 'big') + mdata)


   def recvMessage(self) -> shmessage:
    try:
        header = self._loopRecv(4)
        if not header:
            raise ConnectionResetError("Client disconnected (empty header)")

        size = int.from_bytes(header, 'big')
        payload = self._loopRecv(size).decode('utf-8')

        m = shmessage()
        m.unmarshal(payload)
        return m

    except ConnectionResetError:
        raise 
    except Exception as e:
        raise Exception(f'Bad getMessage: {e}')



   def close(self):
       self._sock.close()