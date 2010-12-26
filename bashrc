unalias -a
alias s='screen'
alias ta='tmux attach'
alias tunpro="ssh -p 25022 adi@proatria.serveftp.com -D 1080 -TNf"
alias tunpro2="ssh -p 15022 adi@proatria.serveftp.com -D 1080 -TNf"
alias sshpro="ssh -p 25022 adi@proatria.serveftp.com"
alias sshpro2="ssh -p 22 adi@proatria.serveftp.com"
alias tt="tsocks telnet"
alias ts="tsocks ssh"
alias tf="tsocks ftp -p"
alias sshu="ssh -p 8003 ubuntu.ro"
alias sshb="ssh -p 8000 baikonur.softwareliber.ro"
alias he="vim ~/.ssh/known_hosts"
alias wo="wget -E -H -k -K -p"
alias wm="wget -m -k -K -E"
function mdcd {
    mkdir $1
    cd $1
}

# Common system task
alias agi="sudo apt-get install"
alias agr="sudo apt-get --purge remove"
alias aar="sudo apt-add-repository"
alias acs="apt-cache search"
alias ags="apt-get source"
alias agu="sudo apt-get update"
alias ae="vim ~/.bashrc ; source ~/.bashrc"
alias se="sudo vim"
alias ab="sudo apt-get build-dep"
alias db="debuild -us -uc -B"
alias ge="gedit"
alias psa="ps -ax"
alias psg="ps -ax | grep"
alias ls="ls --color --group-directories-first"
alias df="df -h --total"
alias du="du -hs"
alias xc="xsel -i -b"
alias sd="xvattr -a XV_CRTC -v"
alias cdd="pushd"
alias scpresume="rsync --partial --progress --rsh=ssh"


# LP stuff
alias rf-get="/home/adi/launchpad/lp-branches/devel/utilities/rocketfuel-get"
alias rf-branch="/home/adi/launchpad/lp-branches/devel/utilities/rocketfuel-branch"
alias rf-push="/home/adi/launchpad/lp-branches/devel/utilities/rocketfuel-push"
alias rf-rtest="/home/adi/launchpad/lp-polyot/polyot-remote-test"
alias rf-rstatus="/home/adi/launchpad/lp-polyot/polyot-remote-status"

alias lp-run="make run"
alias lp-test="LP_PERSISTENT_TEST_SERVICES=1 ./bin/test -vvc -t"
alias lp-tt="LP_PERSISTENT_TEST_SERVICES=1 ./bin/test -vvc -m translations -t"
alias lp-tr="LP_PERSISTENT_TEST_SERVICES=1 ./bin/test -vvc -m registry -t"
alias lp-wt="LP_PERSISTENT_TEST_SERVICES=1 xvfb-run -s '-screen 0 1024x768x24' ./bin/test -vcc"
alias lp-test-translations-pagetest="./bin/test -vvc -m translations --layer PageTestLayer"
alias lp-test-translations-windmill="xvfb-run -s '-screen 0 1024x768x24' ./bin/test --layer=TranslationsWindmillLayer"

# BZR STUFF
alias bzr-diff-submit="bzr diff -r submit: > _diff.diff ; wc -l _diff.diff"
alias bds="bzr diff | wc -l"

# L10N stuff
alias l10n-po-fix="/home/adi/dev/scripts/l10n/validare_po_virgula.sh"
alias l10n-gnome-git-clone="/home/adi/dev/scripts/l10n/gnome-git-clone.sh"
alias l10n-gnome-git-done="/home/adi/dev/scripts/l10n/gnome-git-done.sh"
alias l10n-gnome-git-done-l="/home/adi/dev/scripts/l10n/gnome-git-done-lucian.sh"
alias l10n-gnome-git-done-c="/home/adi/dev/scripts/l10n/gnome-git-done-claudia.sh"
alias l10n-gnome-git-done-d="/home/adi/dev/scripts/l10n/gnome-git-done-dan.sh"

alias l10n-gnome-git-2-30="git checkout --track -b gnome-2-30 origin/gnome-2-30"

# Chevah stuff
alias chevah-code-status="/home/adi/chevah/utils/devel/scripts/chevah-code-status.sh"
alias ccs=chevah-code-status
alias chevah-code-get="/home/adi/chevah/utils/devel/scripts/chevah-code-get.sh"
alias ccg=chevah-code-get
alias chevah-code-push="/home/adi/chevah/utils/devel/scripts/chevah-code-push.sh"
alias ccp=chevah-code-push

export PATH=$PATH:/home/adi/dev/java/ant/bin

export DEBFULLNAME='Adi Roiban'
export DEBEMAIL='adi@roiban.ro'

#export TERM=xterm-256color

export EDITOR=vim

# based on the prompt from
# http://www.gilesorr.com/bashprompt/prompts/twtty.html
function prompt_command {

    TERMWIDTH=${COLUMNS}

    #   Calculate the width of the prompt:
    hostnam=$(echo -n $HOSTNAME | sed -e "s/[\.].*//")
    #   "whoami" and "pwd" include a trailing newline
    #usernam=$(whoami)
    newPWD="${PWD}"
    #   Add all the accessories below ...
    let promptsize=$(echo -n "${USERNAME}@${hostnam} -${PWD}" \
                     | wc -c | tr -d " ")
    let fillsize=${TERMWIDTH}-${promptsize}
    fill=""
    while [ "$fillsize" -gt "0" ] 
    do 
        fill="${fill}-"
	    let fillsize=${fillsize}-1
    done


    if [ "$fillsize" -lt "0" ]
    then
       # if pwd is to large left-truncate it
       let cut=2-${fillsize}
       newPWD="$(echo -n $PWD | sed -e "s/\(^.\{$cut\}\)\(.*\)/\2/")"
       fill=""
       prefill="..."
    else
       # else add a space to hint for a full path
       fill="${fill} "
       prefill=""
    fi
}

PROMPT_COMMAND=prompt_command

function twtty {

local GRAY="\[\033[1;30m\]"
local LIGHT_GRAY="\[\033[0;37m\]"
local WHITE="\[\033[1;37m\]"
local NO_COLOUR="\[\033[0m\]"

local LIGHT_BLUE="\[\033[1;34m\]"
local YELLOW="\[\033[1;33m\]"

PS1="\n$TITLEBAR\
$WHITE\${prefill}$YELLOW\${newPWD} \
$WHITE\${fill}$YELLOW\${USERNAME}$LIGHT_BLUE@$YELLOW\$hostnam\
\n\
$WHITE\$$NO_COLOUR "

PS2="$YELLOW>$NO_COLOUR "
}

twtty
unset twtty
