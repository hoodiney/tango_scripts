import glob
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
from datetime import datetime
import itertools
import pandas as pd
import argparse
import os

# HYPER-PARAMETERS
duration = 24 * 3600 # seconds
samp_interval = 100 # seconds

def parse_args():
    top = argparse.ArgumentParser(description=(
        "plot the coverage to time figures"
    ))
    # top.add_argument('--workdirs', nargs='+',
    #     help="The path to the workdirs to be ploted")
    top.add_argument('-t', "--target",
        help="Name of the target")
    top.add_argument('-o', "--output",
        help="Name of the output file")
    top.add_argument('-f', "--fuzzer", nargs='+', default=["aflnet", 
        "aflnet_no_state", "aflpp", "nyx", "nyx_aggressive", "nyx_balanced"],
        help="Name of the fuzzers")
    return top.parse_args()

# use this function to reduce the size of cov_list, sample it according to a interval
def sample_cov(cov_list):
    sample_cov_list = []
    for i in range(duration // samp_interval):
        idx = i * samp_interval
        sample_cov_list.append(cov_list[idx])
    return sample_cov_list

def read_sancov(file_path):
    pc_set = []
    with open(file_path, "rb") as file:
        byte = file.read(1)
        if int.from_bytes(byte, "little") == 0x64:
            pc_length = 8
        else:
            pc_length = 4
        byte = file.read(7)
        while byte:
            byte = file.read(pc_length)
            pc_set.append(hex(int.from_bytes(byte, "little")))
    return set(pc_set[:-1])

# need to replace some characters ("," ":")
def process_seed_name(name):
    new_name = name.replace(",", "_")
    new_name = new_name.replace(":", "_")
    return new_name

# return a list for all seconds in 24 hrs data of one workdir
def process_workdir(workdir_path):
    # get all inputs and the timestamps in the queue
    cov_info = {}
    seed_files = []
    if_init = False
    for _,_,files in os.walk(os.path.join(workdir_path, "queue")):
        files = [os.path.join(workdir_path, "queue", file) for file in files]
        files.sort(key=os.path.getmtime)
        for file in files:
            seed_files.append(file)
            create_time = datetime.fromtimestamp(os.path.getmtime(file))
            
            if not if_init:
                init_time = create_time
                cov_info[file] = 0
                if_init = True
            else:
                cov_info[file] = (create_time - init_time).total_seconds()
        break
    # get time2cov
    time2cov = {}
    pc_set = set()
    for file in seed_files:
        file_name = file.split("/")[-1]
        sancov_folder_path = os.path.join(workdir_path, "fs/shared", process_seed_name(file_name) + "_sancov_dir")
        if os.listdir(sancov_folder_path):
            sancov_file_path = os.path.join(sancov_folder_path, os.listdir(sancov_folder_path)[0])
            temp_pc_set = read_sancov(sancov_file_path)
        else:
            print("{} has no sancov file".format(file))
            temp_pc_set = set()
        pc_set = pc_set.union(temp_pc_set)
        time2cov[cov_info[file]] = len(pc_set)
        # cov_info[file]["pc_cov_cnt"] = len(pc_set)
    # now get the coverage list of the data per second
    
    last_cov = 0
    cov_list = []
    for i in range(duration):
        if i in time2cov:
            last_cov = time2cov[i]
        
        cov_list.append(last_cov)
    return cov_list

def get_mean_std(list_of_runs):
    arrays = [np.array(x) for x in list_of_runs]
    cov_means = [np.mean(k) for k in zip(*arrays)]
    cov_stds = [np.std(k) for k in zip(*arrays)]
    return cov_means, cov_stds

# merge the data from all five iterations, return resampled data in the form of cov_list
def process_all_workdirs(target, fuzzer):
    # construct workdir_paths according to the target and fuzzer name
    workdir_paths = []
    for i in range(5):
        workdir_name = "out-{}-{}-00{}".format(target, fuzzer, i)
        # if "nyx" in fuzzer or "aflpp" in fuzzer:
        #     workdir_name = "new-" + workdir_name
        workdir_paths.append(os.path.join("targets", target, workdir_name))

    cov_lists = []
    for workdir_path in workdir_paths:
        # only add sampled cov_lists, so as to be more efficient in getting mean and std
        cov_lists.append(sample_cov(process_workdir(workdir_path)))

    times = [[i * samp_interval for i in range(duration // samp_interval)] for j in range(len(workdir_paths))]
    merged_time_list = list(itertools.chain(*times)) 
    merged_cov_list = list(itertools.chain(*cov_lists))

    cov_df = pd.DataFrame(
        {
            'time': merged_time_list,
            'coverage': merged_cov_list,
            'fuzzer': fuzzer
        }
    )

    return cov_df

# merge the data from all five iterations, return resampled data in the form of cov_list
# def process_all_workdirs(target, fuzzer):
#     # construct workdir_paths according to the target and fuzzer name
#     workdir_paths = []
#     for i in range(1):
#         workdir_name = "out-{}-{}-00{}".format(target, fuzzer, i)
#         # if "nyx" in fuzzer or "aflpp" in fuzzer:
#         #     workdir_name = "new-" + workdir_name
#         workdir_paths.append(os.path.join("targets", target, workdir_name))

#     cov_lists = []
#     for workdir_path in workdir_paths:
#         # only add sampled cov_lists, so as to be more efficient in getting mean and std
#         cov_lists.append(sample_cov(process_workdir(workdir_path)))

#     times = [[i * samp_interval for i in range(duration // samp_interval)] for j in range(len(workdir_paths))]
#     merged_time_list = list(itertools.chain(*times)) 
#     merged_cov_list = list(itertools.chain(*cov_lists))

#     cov_df = pd.DataFrame(
#         {
#             'time': merged_time_list,
#             'coverage': merged_cov_list,
#             'fuzzer': fuzzer
#         }
#     )

#     return cov_df

def plot_one(args):
    fig, axes = plt.subplots(figsize=(20, 10))
    axes.set(xlabel='Time (seconds)')
    axes.set(ylabel='Edge Coverage')
    axes.set_title('Coverage Over Time ({})'.format(args.target))

    cov_df_list = []
    for fuzzer in args.fuzzer:
        cov_df_list.append(process_all_workdirs(args.target, fuzzer))
    
    cov_df = pd.concat(cov_df_list)
    axes = sns.lineplot(data=cov_df, y='coverage', x='time', hue="fuzzer", errorbar=('ci', 95))
    print("ploted")

    # svg_name = "cov_time_{}".format(args.target)
    # for fuzzer in args.fuzzer:
    #      svg_name += "_{}".format(fuzzer)
    # svg_name += ".svg"     

    fig.savefig(args.output, format="svg")   

# def plot_tango_others(args):
#     cov_df_others_list = []
#     cov_df_tango_list = []
#     for fuzzer in args.fuzzer:
#         if "tango" in fuzzer:
#             cov_df_tango_list.append(process_all_workdirs(args.target, fuzzer))
#         else:
#             cov_df_others_list.append(process_all_workdirs(args.target, fuzzer))
#     cov_others_df = pd.concat(cov_df_others_list)
#     cov_tango_df = pd.concat(cov_df_tango_list)

#     cov_others_df = cov_others_df.rename(columns={"coverage": "coverage_others"})
#     cov_tango_df = cov_tango_df.rename(columns={"coverage": "coverage_tango"})
    
#     fig, axes = plt.subplots(1, 2, sharey=True, figsize=(24, 10))
    
#     axes[0] = sns.lineplot(ax=axes[0], data=cov_others_df, \
#                         y='coverage_others', x='time', hue="fuzzer", errorbar=('ci', 95))
#     axes[1] = sns.lineplot(ax=axes[1], data=cov_tango_df, \
#                         y='coverage_tango', x='time', hue="fuzzer", errorbar=('ci', 95))

#     # plt.tight_layout()
#     fig.suptitle('Coverage Over Time ({})'.format(args.target))
#     axes[0].set_xlabel('Time (seconds)')
#     axes[0].set_ylabel('Edge Coverage')

#     axes[1].set_xlabel('Time (seconds)')
#     axes[1].set_ylabel('Edge Coverage')

#     fig.savefig(args.output, format="svg")   


def plot_tango_others(args):
    cov_df_others_list = []
    cov_df_tango_list = []
    for fuzzer in args.fuzzer:
        if "tango" in fuzzer:
            cov_df_tango_list.append(process_all_workdirs(args.target, fuzzer))
        else:
            cov_df_others_list.append(process_all_workdirs(args.target, fuzzer))
    cov_others_df = pd.concat(cov_df_others_list)
    cov_tango_df = pd.concat(cov_df_tango_list)

    fig = plt.figure(figsize=(24, 10))
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2, sharey=ax1)
    
    cov_others_df = cov_others_df.rename(columns={"coverage": "coverage_others"})
    cov_tango_df = cov_tango_df.rename(columns={"coverage": "coverage_tango"})
    
    sns.lineplot(ax=ax1, data=cov_others_df, \
                        y='coverage_others', x='time', hue="fuzzer", errorbar=('ci', 95))
    sns.lineplot(ax=ax2, data=cov_tango_df, \
                        y='coverage_tango', x='time', hue="fuzzer", errorbar=('ci', 95))

    # plt.tight_layout()
    fig.suptitle('Coverage Over Time ({})'.format(args.target))
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Edge Coverage')

    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Edge Coverage')

    fig.savefig(args.output, format="svg")   

def plot_tango(args):
    # cov_df_others_list = []
    cov_df_tango_list = []
    for fuzzer in args.fuzzer:
        cov_df_tango_list.append(process_all_workdirs(args.target, fuzzer))
    # cov_others_df = pd.concat(cov_df_others_list)
    cov_tango_df = pd.concat(cov_df_tango_list)


    fig, axes = plt.subplots(figsize=(20, 10))
    axes.set(xlabel='Time (seconds)')
    axes.set(ylabel='Edge Coverage')
    axes.set_title('Coverage Over Time ({})'.format(args.target))
    
    cov_tango_df = cov_tango_df.rename(columns={"coverage": "coverage_tango"})
    
    sns.lineplot(data=cov_tango_df, \
                        y='coverage_tango', x='time', hue="fuzzer", errorbar=('ci', 95))

    fig.savefig(args.output, format="svg")   


def main():
    # now plot the figures
    args = parse_args() 
    # fig, axes = plt.subplots(figsize=(20, 10))
    # axes.set(xlabel='Time (seconds)')
    # axes.set(ylabel='Edge Coverage')
    # axes.set_title('Coverage Over Time ({})'.format(args.target))

    # cov_df_list = []
    # for fuzzer in args.fuzzer:
    #     cov_df_list.append(process_all_workdirs(args.target, fuzzer))
    
    # cov_df = pd.concat(cov_df_list)
    # axes = sns.lineplot(data=cov_df, y='coverage', x='time', hue="fuzzer", errorbar=('ci', 95))
    # print("ploted")

    # svg_name = "cov_time_{}".format(args.target)
    # for fuzzer in args.fuzzer:
    #      svg_name += "_{}".format(fuzzer)
    # svg_name += ".svg"     

    # fig.savefig(args.output, format="svg")   
    plot_tango(args)


if __name__ == "__main__":
    main()