from fec.linker import *

Linker().link()

#import cProfile
#import pstats
#cProfile.run('Linker().link()', 'prof')
#p = pstats.Stats('prof')
#p.sort_stats('cumulative').print_stats(50)