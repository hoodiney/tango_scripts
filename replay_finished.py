import os
import argparse

def parse_args():
    top = argparse.ArgumentParser(description=(
        "check if the workdirs of a target have all been processed"
    ))
    top.add_argument('-t', "--target", 
        help="The path to the TangoFuzz fuzz.json file.")
    top.add_argument('-w', "--workdirs", nargs='+',
        help="relative path to the workdirs.")
    return top.parse_args()

# need to replace some characters ("," ":")
def process_seed_name(name):
    new_name = name.replace(",", "_")
    new_name = new_name.replace(":", "_")
    return new_name

def check_workdir(target, workdir):
    queue_path = os.path.join(workdir, "queue")
    if not os.path.exists(queue_path):
        print(queue_path)
        return None, None
    shared_dir_path = os.path.join(workdir, "fs/shared")
    # only keep file seed names, excluding folders
    seeds = [] 
    for seed in os.listdir(queue_path):
        seed_path = os.path.join(queue_path, seed)
        if not os.path.isdir(seed_path):
            seeds.append(seed)

    not_processed = []
    for seed in seeds:
        sancov_dir_path = os.path.join(shared_dir_path, "{}_sancov_dir".format(process_seed_name(seed)))
        if not os.path.exists(sancov_dir_path) or not os.listdir(sancov_dir_path):
            not_processed.append(seed)
    return not_processed, len(seeds)

def main():
    args = parse_args()
    # get seeds in queue
    # workdirs = [
    #     "out-{}-aflnet-00".format(args.target),
    #     "out-{}-aflnet_no_state-00".format(args.target),
    #     "new-out-{}-aflpp-00".format(args.target),
    #     "new-out-{}-nyx-00".format(args.target),
    #     "new-out-{}-nyx_aggressive-00".format(args.target),
    #     "new-out-{}-nyx_balanced-00".format(args.target)
    # ]

    is_finished = True
    for workdir in args.workdirs:
        not_processed, seeds_num = check_workdir(args.target, workdir)
        
        if not_processed is None or not_processed:
            print(not_processed)
            is_finished = False
            print(is_finished)
            return

        # for i in range(7):
        #     not_processed, seeds_num = check_workdir(args.target, workdir + str(i))
        #     # if not_processed:
        #     #     print(workdir + str(i), "{}/{}".format(len(not_processed), seeds_num))
        #     # else:
        #     #     print(workdir + str(i), "finished")
        #     if not_processed:
        #         print(not_processed)
        #         is_finished = False
        #         print(is_finished)
        #         return
    print(is_finished)

if __name__ == "__main__":
    main()

