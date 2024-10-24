import customfloat

f = 3.14
a = float()
b = float(3)
c = float('2.3')
# print(f)  # This will trigger the custom float_repr
# hash(f)   # This will trigger the custom float_hash
# f == 3.14  # This will trigger the custom float_richcompare
# f + 1.0    # Would trigger the patched vectorcall, if applicable


g = sorted.__new__(sorted, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
print(g)