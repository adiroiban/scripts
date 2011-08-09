#!/bin/bash

# Call this script with `timeout` to avoid infinite locking.

# Paths must end with a trailing slash ('/').
# AFAIK bzr-svn only supports svn and svn+ssh ... or I don't know how to
# use bzr with bzr+file.
SVN_URL='svn+ssh://localhost/home/adi/tmp/svn-mirror/'

# Local path to BZR mirror base folder.
BZR_MIRROR_ROOT='/home/adi/tmp/bzr-mirror/'

# Folder used for locking bzr sync process.
# The process should have rights for creating and deleting the folder.
SYNC_LOCK='/tmp/bzr-sync.lock'

# Number of second after which to retry obtaining a lock.
WAIT_FOR_LOCK_SECONDS=1

# Number of times to retry obtaining a lock.
WAIT_FOR_LOCK_COUNT=30

TRUNK_FOLDER="trunk/"
BRANCHES_FOLDER="branches/"
SVNLOOK_BIN=`which svnlook`
BZR_BIN=`which bzr`
MKDIR_BIN=`which mkdir`
RM_BIN=`which rm`

# Sample ouput from svnlook.
#
# A branch was added
# -------------------
# A   branches/feat2/
#
# A file in a branch was added
# ----------------------------
# A   branches/feat2/raca
#
# A property in a branch was updated
# ----------------------------------
# _U  branches/feat2/raca
#
# A file and property in a branch was updated
# -------------------------------------------
# UU  branches/feat2/raca
#
# A branch was deleted
# --------------------
# D   branches/feat1/
#
# Some files in trunk were updated
# --------------------------------
# D   trunk/caca.file
# U   trunk/raca
# _U  trunk/daca


# Instead of using an array, the branches are added in the queue as strings
# delimited by '|'.
# The string "array" is initialized with '|' and then each branch name will be
# added with a trailing '|'.
deleted_branches='|'
added_branches='|'
updated_branches='|'
update_trunk_needed='no'

check_mirror_structure() {
    # Check that mirror folders (root and branches root) exists.
    # If trunk folder is missing it will be created by update_trunk.
    mirror_path=${BZR_MIRROR_ROOT}
    if [ ! -d $mirror_path ]
    then
        $MKDIR_BIN -p $mirror_path
    fi

    branches_path=${BZR_MIRROR_ROOT}${BRANCHES_FOLDER}
    if [ ! -d $branches_path ]
    then
        $MKDIR_BIN -p $branches_path
    fi
}


queue_add_branch() {
    # Add brach into queue, if it was not already added.
    branch_name=$1
    if [[ $added_branches != *\|$branch_name\|* ]]
    then
        added_branches="$added_branches$branch_name|"
    fi
}


add_queued_branches() {
    # Strip leading and trailing |, before changing IFS.
    queue=$1
    queue=${queue#|}
    queue=${queue%|}
    OIFS=$IFS
    IFS='|'
    for branch in $queue
    do
        add_branch $branch
    done
    IFS=$OIFS
}


queue_delete_branch() {
    # Add brach into queue, if it was not already in the queue.
    branch_name=$1
    if [[ $deleted_branches != *\|$branch_name\|* ]]
    then
        deleted_branches="$deleted_branches$branch_name|"
    fi
}


delete_queued_branches() {
    # Strip leading and trailing |, before changing IFS.
    queue=$1
    queue=${queue#|}
    queue=${queue%|}
    OIFS=$IFS
    IFS='|'
    for branch in $queue
    do
        delete_branch $branch
    done
    IFS=$OIFS
}


queue_update_branch() {
    # Add brach into updated queue, if it was not already in the deleted
    # or added queues.
    branch_name=$1

    if [[ $added_branches = *\|$branch_name\|* ]]
    then
        return
    fi

    if [[ $deleted_branches = *\|$branch_name\|* ]]
    then
        return
    fi

    if [[ $updated_branches != *\|$branch_name\|* ]]
    then
        updated_branches="$updated_branches$branch_name|"
    fi
}


update_queued_branches() {
    # Strip leading and trailing |, before changing IFS.
    queue=$1
    queue=${queue#|}
    queue=${queue%|}
    OIFS=$IFS
    IFS='|'
    for branch in $queue
    do
        update_branch $branch
    done
    IFS=$OIFS
}


update_trunk() {
    do_update=$1
    if [ "$do_update" = "no" ]
    then
        return
    fi

    # If trunk folder does not exists we add it instead of updating it.
    trunk_path=${BZR_MIRROR_ROOT}${TRUNK_FOLDER}
    if [ ! -d $trunk_path ]
    then
        $BZR_BIN branch $SVN_URL${TRUNK_FOLDER} $trunk_path
    else
        cd $trunk_path
        $BZR_BIN pull $SVN_URL${TRUNK_FOLDER}
    fi
}


update_branch() {
    # Pull changes from a branch.
    # If the branch forlder does not exists, the branch is created.
    branch_name=$1
    branch_folder=${BZR_MIRROR_ROOT}${BRANCHES_FOLDER}$branch_name
    if [ -d $branch_folder ]
    then
        cd ${BZR_MIRROR_ROOT}${BRANCHES_FOLDER}$branch_name
        $BZR_BIN pull $SVN_URL${BRANCHES_FOLDER}$branch_name
    else
        add_branch $branch_name
    fi
}


add_branch() {
    branch_name=$1
    remote_url=$SVN_URL${BRANCHES_FOLDER}$branch_name
    local_path=${BZR_MIRROR_ROOT}${BRANCHES_FOLDER}$branch_name
    $BZR_BIN branch $remote_url $local_path
}


delete_branch() {
    branch_name=$1
    $RM_BIN -rf ${BZR_MIRROR_ROOT}${BRANCHES_FOLDER}$branch_name
}

obtain_lock_or_wait () {
    retry_count=0
    while true
    do
        if mkdir ${SYNC_LOCK}
        then
            # Set trap to remove lock on exit.
            trap "{ rm -rf ${SYNC_LOCK} ; exit 255; }" EXIT
            break;
        fi
        let retry_count=$retry_count + 1
        if [[ $retry_count < WAIT_FOR_LOCK_COUNT ]]
        then
            exit
        fi
        sleep ${WAIT_FOR_LOCK_SECONDS}
    done
}

release_lock () {
    rmdir ${SYNC_LOCK}
}


svn_changes=`$SVNLOOK_BIN changed $1 -r $2`
while read change
do
    action=${change%% *}
    path=${change##* }

    # Any change starting with 'trunk' will trigger a trunk update.
    if [[ "$path" = ${TRUNK_FOLDER}* ]]
    then
        update_trunk_needed="yes"
    fi

    # Look for changes starting with branches folder.
    if [[ "$path" = ${BRANCHES_FOLDER}* ]]
    then
        branch_name=${path##${BRANCHES_FOLDER}}
        branch_name=${branch_name%%/*}

        # Look for changes to root branches (add/delete).
        if [[ "$path" =~ ${BRANCHES_FOLDER}[^/]+/$ ]]
        then
            if [[ "$action" = "A" ]]
            then
                queue_add_branch $branch_name
            elif [[ "$action" = "D" ]]
            then
                queue_delete_branch $branch_name
            else
                queue_update_branch $branch_name
            fi
        else
            # Any change inside a branch will trigger an update.
            queue_update_branch $branch_name
        fi
    fi
done <<< $svn_changes

check_mirror_structure
update_trunk $update_trunk_needed

obtain_lock_or_wait

add_queued_branches $added_branches
delete_queued_branches $deleted_branches
update_queued_branches $updated_branches

release_lock
