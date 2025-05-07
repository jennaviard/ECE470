from enum import Enum

class WAVEREQ(Enum):
    CRE8 = 200
    JOIN = 201
    GLST = 202
    STRT = 203
    CARD = 204
    CLUE = 205
    GUESS = 206
    BONUS = 207
    SCRB = 208
    NEXT = 209
    ENDG = 210
    CHAT = 211

class shmessage(object):
    PJOIN = '&'
    VJOIN = '{}={}'
    VJOIN1 = '='

    def __init__(self):
        self._data = {}
        self._data['type'] = WAVEREQ.CRE8

    def __str__(self) -> str:
        return self.marshal()

    def reset(self):
        self._data = {}
        self._data['type'] = WAVEREQ.CRE8

    def setType(self, t):
        self._data['type'] = t

    def getType(self):
        return self._data['type']

    def addValue(self, key: str, value: str):
        self._data[key] = value

    def getValue(self, key: str) -> str:
        return self._data.get(key, None)

    def marshal(self) -> str:
        pairs = [shmessage.VJOIN.format(k, v) for (k, v) in self._data.items()]
        return shmessage.PJOIN.join(pairs)

    def unmarshal(self, d: str):
        self.reset()
        if d:
            params = d.split(shmessage.PJOIN)
            for p in params:
                k, v = p.split(shmessage.VJOIN1, 1)
                if k == 'type':
                    enum_str = v.split('.')[-1]
                    self._data['type'] = WAVEREQ[enum_str]
                else:
                    self._data[k] = v