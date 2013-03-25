from optparse import OptionParser
from fec.linker import *

parser = OptionParser()
parser.add_option("-d", "--db", dest="dbname",
                  default="fec",
                  help="Database name with data to link")
parser.add_option("-t", "--table",
                  default="individual_contributions",
                  help="Name of table to link")
(options, args) = parser.parse_args()

Linker(options.dbname, options.table).link()

#import cProfile
#import pstats
#cProfile.run('Linker().link()', 'prof')
#p = pstats.Stats('prof')
#p.sort_stats('cumulative').print_stats(50)