# hiim_pipeline

A data analysis pipeline to process MeerKAT data for interferometric HI intensity mapping

Calibration based mostly on [oxcat](https://github.com/IanHeywood/oxkat) and some on [processmeerkat](https://github.com/idia-astro/pipelines).

Use [hiimtool](https://github.com/zhaotingchen/hiimtool) for dependencies

## Example Usage
In the working dir, generate a config file `config.ini` (see [example config file](config.ini)). First run

```bash
python path/to/hiim_pipeline/interim/gen_dir.py config.ini
```

which generates the folders to store the output. Note that this only requires basic python3 and can be run on a minimum interative slurm session.

To generate the slurm jobs, run

```bash
python path/to/hiim_pipeline/interim/set_0GC.py config.ini
```

which will generate 0GC tasks in the folder specificed in the `OUTPUT/script`. Similar for 1GC and 2GC. Then simply submit the jobs in the numbered order for actually processing the data. Automated final bash script for submitting the jobs will be added in the future.

Currently only 0GC and 1GC are tested.