import customlist
customlist.install_custom_methods()

a = int('32')
print(a)

a = []
a.append("hello")
a.append("wrf")
a.append("hhhsdf")
a.append("blala")

customlist.uninstall_custom_methods()


b = {1:"hello", 2: "world"}
a.append(b)

customlist.install_custom_methods()


c = []
c.append(5)
print(a)  # Should show: ['~~~~hello~~~~']

# a.sort()

# A function that returns the 'year' value:
def myFunc(e):
  return e['year']

cars = [
  {'car': 'Ford', 'year': 2005},
  {'car': 'Mitsubishi', 'year': 2000},
  {'car': 'BMW', 'year': 2019},
  {'car': 'VW', 'year': 2011}
]

cars.sort()