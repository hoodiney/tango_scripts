from datetime import datetime
import argparse
import os

def parse_args():
    top = argparse.ArgumentParser(description=(
        "distill and merge the coverage data to a csv file"
    ))
    # top.add_argument('--workdirs', nargs='+',
    #     help="The path to the workdirs to be ploted")
    top.add_argument('-t', "--tuple", nargs='+', 
        help="tuples in the form of (target,fuzzer,relative_path_to_workdir)")
    top.add_argument('-o', "--output",
        help="Name of the output file")
    top.add_argument('-n', "--num", 
        help="number of the maximum iterations among all workdirs")
    return top.parse_args()

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

def process_workdir_no_sample(workdir_path):
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
        temp_pc_set = set()
        if os.listdir(sancov_folder_path):
            # if we need to consider the shared libraries
            for sancov_file in os.listdir(sancov_folder_path):
                if ".so." in sancov_file:
                    continue
                sancov_file_path = os.path.join(sancov_folder_path, sancov_file)
                temp_pc_set = temp_pc_set.union(read_sancov(sancov_file_path))
        else:
            print("{} has no sancov file".format(file))
        pc_set = pc_set.union(temp_pc_set)
        time2cov[cov_info[file]] = len(pc_set)
        # cov_info[file]["pc_cov_cnt"] = len(pc_set)
    # now get the coverage list of the data per second
    return time2cov

def get_all_data(target, fuzzer, workdir_path, num):
    cov_df_list = []
    for i in range(num):
        workdir_path_new = "{}-00{}".format(workdir_path, i)
        # if "nyx" in fuzzer or "aflpp" in fuzzer:
        #     workdir_name = "new-" + workdir_name
        if os.path.exists(workdir_path_new):
            time2cov = process_workdir_no_sample(workdir_path_new)
            time_list = []
            cov_list = []
            for time, cov in time2cov.items():
                time_list.append(time)
                cov_list.append(cov)
            cov_df = pd.DataFrame(
                {
                    'fuzzer': fuzzer,
                    'target': target,
                    'run': i,
                    'time': time_list,
                    'coverage': cov_list
                }
            )
            cov_df_list.append(cov_df)
            # workdir_paths.append(os.path.join("targets", target, workdir_name))
    return cov_df_list

def get_tuples(args):
    target_dict = {}
    for tuple_string in args.tuple:
        strings = tuple_string.replace("(", "").replace(")", "").split(",")
        target = strings[0]
        fuzzer = strings[1]
        workdir_path = strings[2]
        if target in target_dict:
            target_dict[target][fuzzer] = workdir_path
        else:
            target_dict[target] = {fuzzer: workdir_path}
    return target_dict

# dump the coverage info of all campaigns to csv
def dump_all_data(args):
    target_dict = get_tuples(args)
    cov_df_list = []

    for target, fuzzer_dict in target_dict.items():
        for fuzzer, workdir_path in fuzzer_dict.items():
            cov_df_list += get_all_data(target, fuzzer, workdir_path, int(args.num))
    
    cov_df = pd.concat(cov_df_list)
    cov_df.to_csv(args.output, index=False)

def main():
    args = parse_args() 
    dump_all_data(args)


if __name__ == "__main__":
    main()