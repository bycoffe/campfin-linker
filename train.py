import os
from fec.trainer import *

if not os.path.isfile("data/crp_slice.csv"):
    os.system("unzip data/crp_slice.zip -d data")

Trainer().generate_training_set()