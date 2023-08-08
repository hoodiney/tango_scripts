# Scripts
├── **gen_cov.py**: replay the seeds in the queue of a target's workdir.  

├── **gen_cov.sh**: replay for all the appointed workdirs, until finished. 

├── **plot_cov.py**: plot the coverage to time plots for the appointed workdirs.

└── **replay_finished.py**: ensure all seeds in a queue are replayed.

# Usage
## gen_cov.sh
gen_cov.sh assumes each (fuzzer, target) pair has 5 iterations, and replay for all 5 iterations in parallel. Convention of the workdir naming should be something like **out-\$target-\$fuzzer-000** (out-expat-tango-000)

```
./gen_cov.sh $target $fuzzer
```
**target**: expat, openssh, etc.

**fuzzer**: name of the fuzzer. 

## plot_cov.py
plot_cov.py follows the same workdir naming convention as gen_cov.sh's. 

```
python plot_cov.py -t expat -o out.svg -f tango tango-mode0 tango-mode1
```
**-t**: target name

**-o**: output plot file name

**-f**: fuzzer names
