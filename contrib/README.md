# How to run

Running datatrove on juwels-cluster

Begin with pip-installing this package:

```
pip install .
```

preferrably in a virtual environment of your choosing.

After this, run the following to get the tldextract cache (otherwise each task will try to download it, leading to errors and failed runs):

```
env TLDEXTRACT_CACHE="tldextract.cache" tldextract --update
```

Then, edit the `run_pipeline.sh`-script. In particular, make sure of the following:
- That the `TLDEXTRACT_CACHE` directory points to the tldextract.cache you just downloaded,
- That you source the appropriate virtual environment. 
- That you point to the correct input and output directory. 

Then, run 

```
sbatch run_pipeline.sh
```
