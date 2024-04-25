import customlist
customlist.install_custom_append()

a = []
a.append("hello")
a.append("wrf")
a.append("hhhsdf")
a.append("blala")

b = {1:"hello", 2: "world"}
a.append(b)
print(a)  # Should show: ['~~~~hello~~~~']