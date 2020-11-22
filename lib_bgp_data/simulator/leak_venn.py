# NOTE: this script is meant to be run as a standalone without this lib, developing rn so just gonna stick it ehere


# pip3 install matplotlib-venn
from matplotlib import pyplot as plt
#from matplotlib_venn import venn3
from leaks import prepending, loops, multileak, single_leak

# https://github.com/tctianchi/pyvenn
"""
set1 = set(['A', 'B', 'C', 'D'])
set2 = set(['B', 'C', 'D', 'E'])
set3 = set(['C', 'D',' E', 'F', 'G'])

print(len(loops.intersection(prepending)))
venn3([set1, set2, set3], ('Set1', 'Set2', 'Set3'))
plt.show()
venn3([prepending, loops, multileak], ("prepending", "loops", "multileak"))
plt.show()
"""
import matplotlib
#matplotlib.use('Agg')
from pyvenn import venn

labels = venn.get_labels([prepending, loops, multileak, single_leak], fill=["number", "percent"])
#labels = venn.get_labels([range(10), range(5, 15), range(3, 8), range(8, 17)], fill=['number', 'logic'])

fig, ax = venn.venn4(labels, names=['prepending', 'loops', 'multileak', 'single_leak'])
print("here")
fig.show()
plt.show()
