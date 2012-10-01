#sudo apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 4E5E17B5
#sudo add-apt-repository ppa:chromium-daily
#sudo add-apt-repository ppa:sinzui/ppa

# Faenza
sudo add-apt-repository 'ppa:tiheum/equinox'

# Kupfer
sudo add-apt-repository 'ppa:kupfer-team/ppa'

# Pogo
sudo add-apt-repository ppa:pogo-dev/daily

sudo apt-get update
sudo apt-get remove --purge gwibber thunderbird
sudo apt-get install vim-nox devilspie mc htop leafpad meld chromium-browser \
                bzr bzr-svn bzr-gtk faenza-icon-theme   \
                subversion python-virtualenv network-manager-openvpn-gnome \
                mysql-server php5-mysql php5-sqlite python-mysqldb \
                nautilus-image-converter gcolor2 pogo curl rdesktop\
                libapache2-mod-php5 kupfer synaptic pidgin\
                tsocks proxychains dh-make devscripts tmux nmap \
                git-core vsftpd putty openssh-server regina-rexx \
		xsel gettext filezilla gimp gitg nodejs

sudo /etc/init.d/apache2 restart
exit
apt-get install gettext devscripts cdbs debhelper gnome-common libgtk2.0-dev \
                libpanel-applet2-dev pkgbinarymangler xvattr

