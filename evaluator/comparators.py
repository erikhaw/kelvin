"""
compare files
 - binary
 - text
    - filters
compare StringIO, BytesIO
compare against generator
image comparator can give us image diff
"""

import io
import re

def apply_filters(token, filters):
    return token
    

def xx(resource, filters=[]):
    with resource:
        for line in resource:
            if line[-1] == '\n':
                yield apply_filters(line[:-1], filters)
            else:
                yield apply_filters(line, filters)

def xxbin(f, block_size=1024):
    with f:
        while True:
            b = f.read(block_size)
            if b == b'':
                break
            yield b


def open_me(resource, mode='t', block_size=None, filters=[]):
    if isinstance(resource, str):
        if mode == 't':
            resource = open(resource)
        elif mode == 'b':
            resource = open(resource, 'rb')
        else:
            raise NotImplementedError("mode not implemented")

    if isinstance(resource, io.TextIOBase):
        return xx(resource, filters)
    elif isinstance(resource, io.IOBase):
        return xxbin(resource, block_size=block_size)
    
    return resource



def text_compare(f1, f2):
    f1 = open_me(f1)
    f2 = open_me(f2)

    errors = []
    for line1, line2 in zip(f1, f2):
        if line1 != line2:
            errors.append(f'{line1} != {line2}')

    
    return (False if errors else True, ''.join(errors))


def binary_compare(f1, f2):
    f1 = BlockGenerator(f1, 1024)
    f2 = BlockGenerator(f2, 1024)

    for a, b in zip(f1, f2):
        #a == b ...
        pass

    return (True, "bytes at offset 0x12 not equals")


def image_compare(f1, f2):
    #if f1 not File:
    #    raise "Only files can be compared"

    #np.array(open(f1).read()).diff(open(f2).read())....

    return (True, "<img src='data:image/png,base64;.....'>")


"""
# tasks/task.py
def init_tests():
    t = Test()
    t.stdout = (i for i in range(100))

#-Werror=array-bounds
#-Qformat_security
# odebirat body za warning?
"""