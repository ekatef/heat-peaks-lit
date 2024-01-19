# heat-peaks-lit

Interactive visualisaiton of results of the cross-sectoral modeling study.

## Installation

After forking and cloning `heat-peaks-lit` repo, the following commands are needed to get the app work.

### Create virtual environment

```bash
mamba env create -f ./heat-peaks-lit/env.yaml
conda activate heat-peaks-lit
```

### Prepare data

The app expects to have the inputs available using the paths specified in `app/pages/utils/config.yaml` as `data_dir` argument. The inputs are the solved cross-sectoral networks organised by sub-folders named according to the scenario names set in the config as `scenario_names`. The expected folder structure looks like follows:

data--|
     |--results--|
                |--flex--|
                         |--networks--|
                                      |--elec_s_48_lcopt__Co2L0.0-24H-T-H_2050.nc


### Build the app

```bash
cd heat-peaks-lit
pip install -e .
make streamlit run app/Introduction.py
```

## Architecture

The project is organised as source files of the tabs placed in `app` folder. Each of the source files is supplemented by a helpers file with `prerun` prefix kept in `app/pages/utils` which task is to extract and pre-process networks data.
