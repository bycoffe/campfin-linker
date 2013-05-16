from optparse import OptionParser
from campfin.linker import *

parser = OptionParser()
parser.add_option("-d", "--db", dest="dbname",
                  default=None,
                  help="Database name with data to link")
parser.add_option("-t", "--table",
                  default=None,
                  help="Name of table to link")
(options, args) = parser.parse_args()

Linker().link(options.dbname, options.table)

#import cProfile
#import pstats
#cProfile.run('Linker().link(options.dbname, options.table)', 'prof')
#p = pstats.Stats('prof')
#p.sort_stats('cumulative').print_stats(50)