import os
from fec.preprocessor import *

if not os.path.isfile("data/crp_slice.csv"):
    os.system("unzip data/crp_slice.zip -d data")

Preprocessor().preprocess("data/crp_slice.csv")