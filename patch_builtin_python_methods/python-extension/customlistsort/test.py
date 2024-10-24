import customlistsort

customlistsort.install_custom_list_sort()

# Now you can test if the patch is effective
# sorted_result = sorted([3, 1, 2])
# print(sorted_result)  # Should trigger the custom logging and then return the sorted list

a = [3, 1, 2]
a.sort()