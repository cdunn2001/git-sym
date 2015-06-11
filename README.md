# Why?
The purpose is to separate big-file caching from revision-control.

From the author of **git-fat**:
> Checking large binary files into a source repository (Git or otherwise) is a bad idea because repository size quickly becomes unreasonable. Even if the instantaneous working tree stays manageable, preserving repository integrity requires all binary files in the entire project history, which given the typically poor compression of binary diffs, implies that the repository size will become impractically large. Some people recommend checking binaries into different repositories or even not versioning them at all, but these are not satisfying solutions for most workflows.

## How is **git-sym** different?
There are several alternatives:
  * https://github.com/jedbrown/git-fat
  * https://github.com/schacon/git-media
  * http://git-annex.branchable.com/
  * https://github.com/github/git-lfs

But all those impose the penalty of checksums on the large files. We assert that check-summing is not absolutely requried to guarantee integrity. These large resources can be uniquely derived from stable URLs (e.g. versioned in Amazon S3 or stored by unique filename somewhere). **git-sym** stores only symlinks in the git repo, not the checksums themselves.

In addition to some faster git operations, **git-sym** also allows symlinking *directories*. We think that is more appropriate for a wide variety of use-cases.

## How are these large files retrieved and cached?
**git-sym** leaves that up to you. The repo author is responsible for providing a **makefile** with a rule for every unique target.

Some of the tools listed above provide a lot of out-of-the-box caching functionality, but we prefer to decouple caching from revision-control.

## Features
These are features which **git-sym** shares in common with **git-fat** (which we also like for some use-cases). *Differences are in italics.*
* Clones of the source repository are small and fast because no binaries are transferred, yet fully functional with complete metadata and incremental retrieval (git clone --depth has limited granularity and couples metadata to content).
* git-bisect works properly even when versions of the binary files change over time, *as long as they have been cached already*.
* selective control of which large files to pull into the local store
* Local fat object stores can be shared between multiple clones, even by different users.
* can easily support fat object stores distributed across multiple hosts, *and potentially anywhere in the world*
* depends only on stock Python and rsync

This feature of **git-fat** is *not* yet in **git-sym**. (It depends on `.gitattributes`. We are looking into that.)
* **git-fat** supports the same workflow for large binaries and traditionally versioned files, but internally manages the "fat" files separately.

These are features of **git-sym** which are missing from some or all of the alternatives.
* **git-sym** can fetch via rsync, curl, wget, an s3 client, a google-drive client, or anything else available in your system.
* **git-sym** allows you to symlink directories, which can simplify your data-management.
* **git-sym** never slows down for check-summing (except for the initial caching).
* **git-sym** works fine in git-submodules.
* **git-sym** is easy to understand.

## Installing
You can run this as a **git** command by calling it `git-sym`
in your `$PATH`. Here is one way:
```
ln -sf `pwd`/git-sym ~/bin/git-sym
```
Alternatively, you can run it directly:
```
python git-sym -h
```

## Basic usage
### For repo users
```
git-sym show
git-sym update
```
### For repo owners
```
git-sym add my_big_file.gif
git commit -m 'git-sym added'
ls -l my_big_file.gif
```
Or more explicitly, and with a rule for retrieval:
```
ln -sf .git_sym/my_big_data.v123.db my_big_data.db
git add my_big_data.db
git commit
cat <<EOF >> git_sym.makefile
my_big_data.v123.db:
        wget http://www.somewhere.com/my_big_data.v123.db
EOF
git-sym update
```

## Examples
These examples explain the basics:

* <https://github.com/cdunn2001/git-sym-test/wiki/Examples>

If you prefer words to shell code:
* <https://github.com/cdunn2001/git-sym/wiki/Details>
* <https://github.com/cdunn2001/git-sym/wiki/Examples>
