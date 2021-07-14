import pickle
import struct

test = {'test1': 'abc', 'test2': 'def'}
test1 = {'test3': 'abc', 'test4': 'def'}
test.update(test1)
pickled = pickle.dumps(test)
structed = struct.pack('>L', len(pickled)) + pickled
data = structed[:struct.calcsize('>L')]
unstructed = struct.unpack('>L', data)
unpickled = pickle.loads(pickled)

print(struct.calcsize('>L'))
print(test)
print(pickled)
print(structed)
print(len(pickled))
print(unstructed)
print(unpickled)