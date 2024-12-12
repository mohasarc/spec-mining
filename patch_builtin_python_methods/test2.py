import customlist
customlist.install_custom_append()

# Create an instance of the custom list

a = []
a.append(1)  # This will print "heeyyy"

b = []

a.append(1)  # This will print "heeyyy"
b.append(2)  # This will print "heeyyy" again

print(a, b)