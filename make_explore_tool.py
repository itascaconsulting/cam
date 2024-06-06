# sklearn_porter is not compatible with the current versions of sklearn or Python
# the following code is a monkey patch to make it work at runtime so modification of the
# sklearn_porter files is not needed.
import sklearn
sklearn.__version__ = "1.4.1"
import sklearn.tree
import sklearn.ensemble
import sklearn.svm
import sklearn.neighbors
import sklearn.neural_network
import json
import sys
sys.modules["sklearn.tree.tree"] = sklearn.tree
sys.modules["sklearn.ensemble.weight_boosting"] = sklearn.ensemble
sys.modules["sklearn.ensemble.forest"] = sklearn.ensemble
sys.modules["sklearn.svm.classes"] = sklearn.svm
sys.modules["sklearn.neighbors.classification"] = sklearn.neighbors
sys.modules["sklearn.neural_network.multilayer_perceptron"] = sklearn.neural_network
json.origional_load = json.load
json.load = lambda f, **kwargs: json.origional_load(f)
from sklearn_porter import Porter
import joblib
import numpy as np
import jinja2
from pathlib import Path
#from create_cases import parameters, long_names

#scaler, mlpr = joblib.load("model_jkf.pkl")
scaler, mlpr = joblib.load("final_model.pkl")


porter = Porter(mlpr, language='js')
output = porter.export(embed_data=False)
lines = output.split("\n")

# the Porter puts in a bunch of lines that cause a problem
# here we programmatically remove them to make the process more reproducible and
# more automated
lines_to_skip = ["if (typeof process",  "if (process", "var features", "var prediction", "console.log", "// Prediction:"]
keep_lines = []
for line in lines:
    l = line.strip()
    keep = True
    for lts in lines_to_skip:
        if l.startswith(lts):
            keep=False
    if keep:
        keep_lines.append(line)

# also we need to drop the last two lines
keep_lines = keep_lines[:-2]

template = """
var xscale_mean = {},
    xscale_scale = {};
"""
ppa = lambda _ : np.array2string(_, separator=",")
scaler_data = template.format(ppa(scaler.mean_), ppa(scaler.scale_))

lines = "\n".join(keep_lines)
lines += scaler_data

print(lines, file=open("explore_tool_data/model.js", "w"))

params = dict()

#params["model_code"]  = lines
#Path('explore_tool_data/sliders.js').read_text()
#params["draw_code"] = Path('explore_tool_data/draw.js').read_text()

params["result_header"] = "Normalized failure load: "
params["variables"] = [f"l{_}" for _ in range(5)]

page_template = Path('explore_tool_data/run.js').read_text()
page = jinja2.Environment().from_string(page_template).render(params)
print(page, file=open("explore_tool_data/run.js", "w"))


page_template = Path('explore_tool_data/explore_template.html').read_text()
page = jinja2.Environment().from_string(page_template).render(params)
print(page, file=open("explore_tool_data/tool3.html", "w"))

import os
for fn in ["run.js", "sliders.js", "model.js"]:
    base, _ = fn.split(".")
    new_name = f"{base}_min.js"
    os.system(f"uglifyjs explore_tool_data/{fn} -o explore_tool_data/{new_name}")

os.system("inliner -m --skip-absolute-urls explore_tool_data/tool3.html > deliver/tool3_min.html")
