import os
from campfin.tester import *

if not os.path.isfile("data/crp_slice.csv"):
    os.system("unzip data/crp_slice.zip -d data")

Tester().run_training_test()
#Tester().run_bucket_test()
