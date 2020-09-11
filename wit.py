import datetime
import filecmp
import os
from pathlib import Path
import random
import shutil
import sys

import matplotlib.pyplot as plt
import networkx as nx


class NoWitError(Exception):
    pass


class CommitIdError(Exception):
    pass


class CheckoutError(Exception):
    pass


class DataNotSaved(Exception):
    def __str__(self):
        text = """"NOT SAFE TO CHECKOUT:
        There are files that were Changed and not been staged for commit
        or files that added for commit and not been committed
        
        '>>wit status' -> for details
        """
        return text


class BranchError(Exception):
    pass


class MergeError(Exception):
    pass


def init():
    working_directory = Path(os.getcwd())
    wit_folder = working_directory / '.wit'
    activated = wit_folder / 'activated.txt'
    paths = (
        wit_folder / 'images',
        wit_folder / 'staging_area'
    )

    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
    
    if not activated.is_file():
        with open(activated, 'w') as act_file:
            act_file.write('master')


def get_wit_dir(directory, start_from_parent=True):
    if not start_from_parent:
        for f in directory.iterdir():
            if '.wit' == f.name:
                return directory
    for wit_dir in directory.parents:
        for f in wit_dir.iterdir():
            if '.wit' == f.name:
                return wit_dir
    return None


def copy(current_dir, new_dir):
    if not current_dir.exists():
        print(f"path does not exist: '{current_dir}'")
    elif current_dir.is_dir():
        try:
            shutil.copytree(current_dir, new_dir)
        except FileExistsError:
            shutil.rmtree(new_dir, ignore_errors=True)
            shutil.copytree(current_dir, new_dir)
    else:
        shutil.copy2(current_dir, new_dir)


def get_from_references(wit_directory):
    references = wit_directory / '.wit' / 'references.txt'
    branches = {}
    if references.is_file():
        with open(references, 'r') as ref_file:
            ref_lines = ref_file.readlines()
        for line in ref_lines:
            branch_name, commit = line.split("=")
            commit = commit.strip()
            if commit == "True":
                commit = True
            elif commit == "False":
                commit = False
            elif commit == "None":
                commit = None
            branches[branch_name.strip()] = commit
    return branches


def make_references(wit_directory, head, master, added):
    references = wit_directory / '.wit' / 'references.txt'
    append_text = ""
    if references.is_file():
        with open(references, 'r') as ref_file:
            _ = [ref_file.readline().strip() for _ in range(3)]
            append_text = ref_file.read()
            
    references_text = f"HEAD={head}\nmaster={master}\nadded={added}\n" + append_text
    with open(references, 'w') as ref_file:
        ref_file.write(references_text)


def add(path):
    if ".wit" in path:
        raise NoWitError("unauthorized path", path)
    path = Path(path)
    working_directory = Path(os.getcwd())
    current_dir = working_directory / path
    wit_directory = get_wit_dir(current_dir)
    if wit_directory is None:
        raise NoWitError("No wit folder found", working_directory)

    staging_area = wit_directory / '.wit' / 'staging_area'
    
    current_dir_str = os.fspath(current_dir)
    wit_dir_str = os.fspath(wit_directory)
    added_path = current_dir_str.replace(wit_dir_str, "")
    new_dir = os.fspath(staging_area) + added_path
    new_dir = Path(new_dir)
    new_dir.parent.mkdir(parents=True, exist_ok=True)

    copy(current_dir, new_dir)

    ref = get_from_references(wit_directory)

    head = ref.get('HEAD')
    master = ref.get('master')
    make_references(wit_directory, head, master, True)


def make_folder_name():
    CHARACTERS = "1234567890abcdef"
    folder_name_list = random.choices(CHARACTERS, k=40)
    folder_name = "".join(folder_name_list)
    return folder_name


def make_commit_id(wit_directory):
    folder_name = make_folder_name()
    commit_id_dir = wit_directory / '.wit' / 'images' / folder_name
    counter = 0
    while commit_id_dir.exists() or counter == 10:
        folder_name = make_folder_name()
        commit_id_dir = wit_directory / '.wit' / 'images' / folder_name
        counter += 1
    if commit_id_dir.exists():
        raise CommitIdError("not found a non existing name for commit_id folder", commit_id_dir)
    return commit_id_dir


def change_branch(wit_directory, activated_branch, change_from, change_to):
    references = wit_directory / '.wit' / 'references.txt'
    old_text = f"{activated_branch}={change_from}"
    new_text = f"{activated_branch}={change_to}"
    with open(references, 'r') as ref_file:
        ref_text = ref_file.read()
    ref_text = ref_text.replace(old_text, new_text)
    with open(references, 'w') as ref_file:
        ref_file.write(ref_text)


def make_commit_text_file(commit_id, head, message):
    date = datetime.datetime.now().ctime()
    commit_text = f"parent={head}\ndate={date}\nmessage={message}"
    with open(os.fspath(commit_id) + ".txt", 'w') as commit_file:
        commit_file.write(commit_text)


def commit(message, parent2=None):
    working_directory = Path(os.getcwd())
    wit_directory = get_wit_dir(working_directory, start_from_parent=False)

    if wit_directory is None:
        raise NoWitError("No wit folder found", working_directory)

    activated = wit_directory / '.wit' / 'activated.txt'
    ref = get_from_references(wit_directory)

    added = ref.get('added') is True
    head = ref.get('HEAD')
    master = ref.get('master')

    if not added:
        print("There was no change in the files")
    else:
        if not activated.is_file():
            raise FileNotFoundError("activated file not found", activated)
        with open(activated, 'r') as act_file:
            activated_branch = act_file.read()
        
        commit_id = make_commit_id(wit_directory)

        if ref.get(activated_branch) == head:
            change_branch(wit_directory, activated_branch, head, commit_id.name)

        if (head == master) and (activated_branch == 'master'):
            make_references(wit_directory, commit_id.name, commit_id.name, False)
        else:
            make_references(wit_directory, commit_id.name, head, False)
        
        if parent2:
            make_commit_text_file(commit_id, head + f",{parent2}", message)
        else:
            make_commit_text_file(commit_id, head, message)

        staging_area_dir = wit_directory / '.wit' / 'staging_area'
        shutil.copytree(staging_area_dir, commit_id)


def deep_comper(comp_obj):
    sub_comps_names = comp_obj.common_dirs
    for name in sub_comps_names:
        yield comp_obj.subdirs[name]
        new_comps = deep_comper(comp_obj.subdirs[name])
        for comp in new_comps:
            yield comp


def to_be_committed_gen(staging_area, commit_id, wit_directory):
    wit_path = os.fspath(wit_directory)
    staging_path = os.fspath(staging_area)

    staging_to_commit = filecmp.dircmp(staging_area, commit_id)
    for name in staging_to_commit.left_only:
        file_path = wit_directory / name
        yield file_path
    for name in staging_to_commit.diff_files:
        file_path = wit_directory / name
        yield file_path
    sub_compers = deep_comper(staging_to_commit)
    for comp in sub_compers:
        for diff in comp.diff_files:
            path = Path(comp.left) / diff
            path = os.fspath(path)
            file_path = path.replace(staging_path, wit_path)
            yield Path(file_path)
        for name in comp.left_only:
            path = Path(comp.left) / name
            path = os.fspath(path)
            file_path = path.replace(staging_path, wit_path)
            yield Path(file_path)


def not_staged_gen(wit_directory, staging_area):
    wit_path = os.fspath(wit_directory)
    staging_path = os.fspath(staging_area)

    witdir_to_staging = filecmp.dircmp(wit_directory, staging_area, ignore=['.wit'])
    for name in witdir_to_staging.diff_files:
        file_path = wit_directory / name
        yield file_path
    sub_compers = deep_comper(witdir_to_staging)
    for comp in sub_compers:
        for name in comp.diff_files:
            path = Path(comp.right) / name
            path = os.fspath(path)
            file_path = path.replace(staging_path, wit_path)
            yield Path(file_path)


def untracked_gen(wit_directory, staging_area):
    wit_path = os.fspath(wit_directory)
    staging_path = os.fspath(staging_area)

    witdir_to_staging = filecmp.dircmp(wit_directory, staging_area, ignore=['.wit'])
    for name in witdir_to_staging.left_only:
        file_path = wit_directory / name
        yield file_path
    sub_compers = deep_comper(witdir_to_staging)
    for comp in sub_compers:
        for name in comp.left_only:
            path = Path(comp.right) / name
            path = os.fspath(path)
            file_path = path.replace(staging_path, wit_path)
            yield Path(file_path)


def staging_files_gen(staging_area, wit_directory):
    wit_path = os.fspath(wit_directory)
    staging_path = os.fspath(staging_area)

    for dirpath, dirnames, filenames in os.walk(staging_area):
        for filename in filenames:
            path = Path(dirpath) / filename
            path = os.fspath(path)
            file_path = path.replace(staging_path, wit_path)
            yield file_path
        for dirname in dirnames:
            path = Path(dirpath) / dirname
            path = os.fspath(path)
            file_path = path.replace(staging_path, wit_path)
            yield file_path 


def status():
    working_directory = Path(os.getcwd())
    wit_directory = get_wit_dir(working_directory, start_from_parent=False)
    if wit_directory is None:
        raise NoWitError("No wit folder found", working_directory)

    staging_area = wit_directory / '.wit' / 'staging_area'

    ref = get_from_references(wit_directory)

    commit_id_name = ref.get('HEAD')
    print(f"commit id: {commit_id_name}")
    print('-' * 40)
    
    print("Changes to be committed:\n")
    if commit_id_name:
        commit_id = wit_directory / '.wit' / 'images' / commit_id_name
        to_be_committed = to_be_committed_gen(staging_area, commit_id, wit_directory)
    else:
        to_be_committed = staging_files_gen(staging_area, wit_directory)
    for file_path in to_be_committed:
        print(file_path)
    print('-' * 40)

    print("Changes not staged for commit:\n")
    not_staged_for_commit = not_staged_gen(wit_directory, staging_area)
    for f in not_staged_for_commit:
        print(f)
    print('-' * 40)

    print("Untracked files:\n")
    untracked = untracked_gen(wit_directory, staging_area)
    for f in untracked:
        print(f)
    print('-' * 40)


def check_status(wit_directory, staging_area):
    ref = get_from_references(wit_directory)
    commit_id_name = ref.get('HEAD')

    to_be_committed = None
    if commit_id_name:
        commit_id = wit_directory / '.wit' / 'images' / commit_id_name
        to_be_committed = to_be_committed_gen(staging_area, commit_id, wit_directory)
    else:
        to_be_committed = staging_files_gen(staging_area, wit_directory)
    
    not_staged_for_commit = not_staged_gen(wit_directory, staging_area)

    to_be_committed_empty = len(list(to_be_committed)) == 0
    not_staged_empty = len(list(not_staged_for_commit)) == 0

    return to_be_committed_empty and not_staged_empty


def make_checkout(commit_id, wit_directory, untracked_list):
    commit_dir = os.fspath(commit_id)
    wit_dir = os.fspath(wit_directory)
    files_in_commit = []

    for dirpath, _, filenames in os.walk(commit_id):
        for filename in filenames:
            commit_file = Path(dirpath) / filename
            commit_file_str = os.fspath(commit_file)
            wit_file = commit_file_str.replace(commit_dir, wit_dir)
            wit_file = Path(wit_file)
            files_in_commit.append(wit_file)
            if wit_file not in untracked_list:
                shutil.copy2(commit_file, wit_file)

    for dirpath, _, filenames in os.walk(wit_directory):
        for filename in filenames:
            wit_file = Path(dirpath) / filename
            if ".wit" not in os.fspath(wit_file):
                if (wit_file not in files_in_commit) and (wit_file not in untracked_list):
                    wit_file.unlink()
    

def checkout(name, check_stat=True):
    working_directory = Path(os.getcwd())
    wit_directory = get_wit_dir(working_directory, start_from_parent=False)
    if wit_directory is None:
        raise NoWitError("No wit folder found", working_directory)

    staging_area = wit_directory / '.wit' / 'staging_area'
    activated = wit_directory / '.wit' / 'activated.txt'

    ref = get_from_references(wit_directory)
    master = ref.get('master')

    branch = ref.get(name)

    if branch:
        commit_id_name = branch
    else:
        commit_id_name = name

    commit_id = wit_directory / '.wit' / 'images' / commit_id_name
    if not commit_id.is_dir():
        raise CheckoutError("commit_id or branch not found", name)

    if not check_status(wit_directory, staging_area) and check_stat:
        raise DataNotSaved()
    untracked = untracked_gen(wit_directory, staging_area)
    untracked_list = list(untracked)
    make_checkout(commit_id, wit_directory, untracked_list)
    make_references(wit_directory, commit_id.name, master, False)

    copy(commit_id, staging_area)
    if branch:
        with open(activated, 'w') as activated_branch:
            activated_branch.write(name)


def get_parent(folder_dir):
    if not folder_dir.is_dir():
        return None
    file_dir = os.fspath(folder_dir) + ".txt"
    file_dir = Path(file_dir)
    if not file_dir.is_file():
        return None

    parent = None
    with open(file_dir, 'r') as f:
        f_lines = f.readlines()
    for line in f_lines:
        if "parent=" in line:
            parent = line.replace("parent=", "").strip()
    if parent == "None":
        return None
    elif "," in parent:
        return parent.split(",")
    else:
        return parent


def get_parents(wit_directory, head):
    parents = {}
    head_dir = wit_directory / '.wit' / 'images' / head
    parent = get_parent(head_dir)
    while parent is not None:
        parents[head] = parent
        if type(parent) is list:
            head = parent[0]
        else:
            head = parent
        head_dir = wit_directory / '.wit' / 'images' / head
        parent = get_parent(head_dir)
    return parents


def make_graph(parents_dict):
    nodes = set()
    edges = []
    for head, parent in parents_dict.items():
        if type(parent) is list:
            for p in parent:
                nodes.add(p[:6])
                edges.append((head[:6], p[:6]))
        else:
            nodes.add(parent[:6])
            edges.append((head[:6], parent[:6]))

    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)

    pos = nx.spring_layout(graph)
    nx.draw_networkx_nodes(graph, pos, node_size=10000)
    nx.draw_networkx_labels(graph, pos)
    nx.draw_networkx_edges(graph, pos, arrowsize=100, edge_color="aqua", width=10)
    plt.show()


def graph():
    working_directory = Path(os.getcwd())
    wit_directory = get_wit_dir(working_directory, start_from_parent=False)
    if wit_directory is None:
        raise NoWitError("No wit folder found", working_directory)

    ref = get_from_references(wit_directory)
    head = ref.get('HEAD')
    master = ref.get('master')

    if head is None:
        print("no commit_id found")
    elif master is None:
        print("no master found")
    else:
        parents = get_parents(wit_directory, head)
        make_graph(parents)


def get_branch(wit_directory, name):
    references = wit_directory / '.wit' / 'references.txt'
    if references.is_file():
        with open(references, 'r') as ref_file:
            ref_lines = ref_file.readlines()
        for line in ref_lines:
            branch_name, commit_id = line.split("=")
            if name == branch_name.strip():
                name = name + '='
                return commit_id.strip()
        return None
    else:
        make_references(wit_directory, None, None, False)
        return None


def add_branch(wit_directory, name):
    references = wit_directory / '.wit' / 'references.txt'
    unauthorized_names = ['HEAD', 'master', 'added', ""]
    if name in unauthorized_names:
        raise BranchError("unauthorized names for branch", name)
    ref = get_from_references(wit_directory)
    commit_id = ref.get('HEAD')
    if commit_id is None:
        print("commit not found")
    else:
        with open(references, 'a') as ref_file:
            ref_file.write(f"{name}={commit_id}\n")


def branch(name):
    working_directory = Path(os.getcwd())
    wit_directory = get_wit_dir(working_directory, start_from_parent=False)
    if wit_directory is None:
        raise NoWitError("No wit folder found", working_directory)
    commit_name = get_branch(wit_directory, name)
    if commit_name is None:
        add_branch(wit_directory, name)
    else:
        print("branch name already exists")


def get_common_ground(parents_1, head1, parents_2, head2):
    parents_1_list = []
    parents_2_list = []
    p1 = head1
    p2 = head2
    while p1 is not None:
        
        if type(p1) is list:
            p1 = p1[0]
        parents_1_list.append(p1)
        p1 = parents_1.get(p1)
    while p2 is not None:
        if type(p2) is list:
            p2 = p2[0]
        parents_2_list.append(p2)
        p2 = parents_2.get(p2)

    for p1 in parents_1_list:
        for p2 in parents_2_list:
            if p1 == p2:
                return p1
    return None


def merge(branch_name):
    working_directory = Path(os.getcwd())
    wit_directory = get_wit_dir(working_directory, start_from_parent=False)
    if wit_directory is None:
        raise NoWitError("No wit folder found", working_directory)
    
    staging_area = wit_directory / '.wit' / 'staging_area'
    if not check_status(wit_directory, staging_area):
        raise DataNotSaved()

    commit_name = get_branch(wit_directory, branch_name)
    if commit_name is None:
        raise CommitIdError("branch not found", branch_name)

    ref = get_from_references(wit_directory)
    head = ref.get("HEAD")
    if head is None:
        raise CommitIdError("HEAD commit not found")

    head_parents = get_parents(wit_directory, head)
    commit_parents = get_parents(wit_directory, commit_name)
    common_ground = get_common_ground(head_parents, head, commit_parents, commit_name)
    if common_ground is None:
        raise MergeError("common ground not found", branch_name)
    
    common_ground_dir = wit_directory / '.wit' / 'images' / common_ground
    commit_id = wit_directory / '.wit' / 'images' / commit_name
    
    wit_path = os.fspath(wit_directory)
    commit_path = os.fspath(commit_id)
    staging_path = os.fspath(staging_area)

    master = ref.get('master')
    make_references(wit_directory, head, master, True)

    changed_files = to_be_committed_gen(commit_id, common_ground_dir, wit_directory)
    for changed_file in changed_files:
        commit_file_path = os.fspath(changed_file).replace(wit_path, commit_path)
        commit_file_path = Path(commit_file_path)
        staging_file_dir = os.fspath(changed_file).replace(wit_path, staging_path)
        staging_file_dir = Path(staging_file_dir)
        if commit_file_path.is_file():
            shutil.copy2(commit_file_path, staging_file_dir)

    message = "--merged--"
    parent2 = commit_name
    commit(message, parent2)

    ref = get_from_references(wit_directory)
    head = ref.get("HEAD")
    checkout(head, check_stat=False)


if len(sys.argv) == 2:
    if sys.argv[1] == "init":
        init()
    elif sys.argv[1] == "status":
        status()
    elif sys.argv[1] == "graph":
        graph()

elif len(sys.argv) >= 3:
    if sys.argv[1] == "add":
        path = sys.argv[2]
        add(path)
    elif sys.argv[1] == "commit":
        message = sys.argv[2:]
        message = " ".join(message)
        commit(message)
    elif sys.argv[1] == "checkout":
        name = sys.argv[2]
        checkout(name)
    elif sys.argv[1] == "branch":
        name = sys.argv[2]
        branch(name)
    elif sys.argv[1] == "merge":
        branch_name = sys.argv[2]
        merge(branch_name)