# Scripts
├── **gen_cov.py**: replay the seeds in the queue of a target's workdir.  

├── **gen_cov.sh**: replay for all the appointed workdirs, until finished. 

├── **merge_cov_data.py**: distill and merge the coverage data to a csv file.

└── **replay_finished.py**: ensure all seeds in a queue are replayed.

# Usage
## gen_cov.sh
gen_cov.sh needs four inputs: target, fuzzer, relative path to the workdir 
(without the ending "-00X"), and the number of iterations.

```
e.g.
./gen_cov.sh openssh tango_nyxnet targets/openssh/out-openssh-tango_nyxnet 7
```
## merge_cov_data.py
merge_cov_data.py can output the merged coverage data into a appointed csv file.
The parameters needed are: tuples of (target,fuzzer,relative path to the workdir 
(without the ending "-00X")), output file name, and maximum number of iterations 
among the workdirs (if targets/openssl/out-openssl-nyxnet has only 4 iterations, 
while the input is 7, it will still work).  

```
python merge_cov_data.py -t "(openssh,tango_nyxnet,targets/openssh/out-openssh-tango_nyxnet)" "(openssh,nyxnet,targets/openssh/out-openssh-nyxnet)" "(dnsmasq,tango_nyxnet,targets/dnsmasq/out-dnsmasq-tango_nyxnet)" "(dnsmasq,tango_nyxnet,targets/dnsmasq/out-dnsmasq-tango_nyxnet)" -o out.csv -n 7
```
