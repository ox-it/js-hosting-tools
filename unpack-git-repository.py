"""
Slightly hacky script to export all heads and tags of a git repo to a
directory.
"""

import itertools
import os
import shutil
import sys
import git


def unpack(sha1, repo, target):
    repo = git.Repo(repo)

    for name in ['heads', 'tags']:
        name = os.path.join(target, name)
        if not os.path.exists(name):
            os.mkdir(name)

    for head in repo.heads:
        unpack_ref(sha1, head, os.path.join(target, 'heads', head.name))
    for tag in repo.tags:
        unpack_ref(sha1, tag, os.path.join(target, 'tags', tag.name))

def unpack_ref(sha1, ref, target):
    unpack_tree(sha1, ref.commit.tree, target)

def unpack_tree(sha1s, tree, target):
    if not os.path.exists(target):
        os.mkdir(target)
    if sha1.get(target) == tree.hexsha:
        return

    extant = set(os.listdir(target))
    seen = set()


    for entry in itertools.chain(tree.trees, tree.blobs):
        seen.add(entry.name)
        entry_target = os.path.join(target, entry.name)
        if entry.name in extant:
            entry_sha1 = sha1.get(entry_target)
            if entry_sha1 == entry.hexsha:
                continue

        if isinstance(entry, git.Tree):
            unpack_tree(sha1, entry, entry_target)
        elif isinstance(entry, git.Blob):
            entry.stream_data(open(entry_target, 'w'))
            sha1[entry_target] = entry.hexsha

    for name in extant - seen:
        if name == '.sha1':
            continue
        path = os.path.join(target, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)

    sha1[target] = tree.hexsha

if __name__ == '__main__':
    repo, target = sys.argv[1:3]

    sha1_filename = os.path.join(target, '.sha1')

    try:
        with open(sha1_filename, 'r') as f:
            for l in f:
                f_sha1, f_name = l.strip().split(' ', 1)
                sha1[f_name] = f_sha1
    except IOError:
        sha1 = {}

    unpack(sha1, repo, target)

    with open(sha1_filename, 'w') as f:
        for f_name, f_sha1 in sha1.items():
            f.write("{} {}\n".format(f_sha1, f_name))

