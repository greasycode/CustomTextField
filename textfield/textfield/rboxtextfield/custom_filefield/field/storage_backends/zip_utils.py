import zipfile, zlib, binascii, struct

class RboxUnZippedFile:
    def __init__(self, buffer):
        self.buffer = buffer

    @property
    def real_filename(self):
        return self.buffer.real_filename

    def __iter__(self):
        cdr = zlib.decompressobj()
        itr = self.buffer.__iter__()
        for chunk in itr:
            yield cdr.decompress(chunk)

    def close(self):
        self.buffer.close()

    def read(self):
        cdr = zlib.decompressobj()
        return cdr.decompress(self.buffer.read())

class RboxZippedFile:
    def __init__(self, buffer):
        self.buffer = buffer

    def __iter__(self):
        buffer = self.buffer
        cmpr = zlib.compressobj()
        while True:
            buf = buffer.read(1024 * 8)
            if not buf:
                break
            if cmpr:
                buf = cmpr.compress(buf)
            yield buf
        buf = cmpr.flush()
        yield buf

    def read(self):
        cdr = zlib.compressobj()
        return cdr.compress(self.buffer.read())
        
    def close(self):
        self.buffer.close()
