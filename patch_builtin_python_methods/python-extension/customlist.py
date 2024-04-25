import customlist
customlist.install_custom_append()

a = []
a.append("hello")
a.append("wrf")
a.append("hhhsdf")
a.append("blala")

b = {1:"hello", 2: "world"}
a.append(b)

c = []
c.append(5)
print(a)  # Should show: ['~~~~hello~~~~']