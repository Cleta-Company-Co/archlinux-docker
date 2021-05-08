from fabric import Connection, Config
from invoke import Responder, watchers
from base_installer_arch import RaspiSSH


class RaspiSSHCommander():

    def __init__(self, host, username, port):
        self.host = host
        self.username = username
        self.port = port

    def obtain_su():
        print("Using super user SU")
        channel.send("su -\n")
        time.sleep(1)
        channel.send(root_password + "\n")
        time.sleep(2)
    
    def exit_command():
        print("Sending exit command")
        channel.send("exit\n")
        time.sleep(1)
    
    def populate_pacman():
        # Run with su
        print("Populating pacman this might take up to 6 minutes.")
        channel.send("pacman-key --init\n")
        time.sleep(3)
        channel.send("pacman-key --populate archlinxarm\n")
        time.sleep(5)

    def update_pacman(command="pacman -Syu --noconfirm", time_override=360, su=True):
        time.sleep(360)  # 6 minutes
        self.channel.send("{}\n".format(command))

    
    def install_sudo():
        # Run with su
        print("Installing sudo")
        channel.send("pacman -S sudo --noconfirm\n")
        time.sleep(5)

        print("Enabling sudoers. Uncommenting wheel")
        channel.send("echo $'\n%wheel ALL=(ALL) ALL' >> /etc/sudoers\n")

    def set_new_user(username="raspi", new_password="ipsar"):
        obtain_su()

        print("Setting up new user")
        channel.send("useradd -m -g users -G wheel -s /bin/bash {}\n".format(username))
        time.sleep(2)
        channel.send("passwd {}\n".format(username))  # change passwd
        time.sleep(1)
        channel.send("{}\n".format(new_password))  # first time
        time.sleep(2)
        channel.send("{}\n".format(new_password))  # confirm passwd
        time.sleep(1)

        print("Activate sudo for new user")
        exit_command()
        channel.send("su {}\n".format(username))
        time.sleep(3)
        channel.send("{}\n".format(new_password))
        time.sleep(3)

    def receive_data(channel):
        return channel.recv(999999)

    def close_channel(channel):
        channel.close()
    

def test_raspberry_update():
    print("print test raspberry update")

    # Connect one raspberry pi
    raspi1 = RaspiSSH(host="192.168.1.2", port=22, username="alarm", password="alarm")
    raspi1.add_root_password("root")
    raspi1.connect_channel()

    print("Expecting whoami command")
    raspi1.example_command()

    print("Sending populate keys")
    raspi1.example_command(["pacman-key --init", "pacman-key --populate archlinuxarm"], su=True)

    print("Sending update pacman")
    raspi1.example_command(["pacman -Syu --noconfirm"], time_override=360, su=True)

    # Bring the Swarm of Pi's
    # raspi1.create_new_user("raspi01")
    # raspi1.add_new_password("ipsar")


def raspi_bridge():
    """Here work commands that already have the users and groups already set up"""
    # Create dict with hostname and ip address
    fullhost = "alarm@192.168.1.243"
    user = "alarm"
    host = "192.168.1.243"
    port = 22
    password = "alarm"
    sudo_password = "root"

    # Create a connection with the default Alarm user and password
    c = Connection("alarm@192.168.1.243", connect_kwargs={'password':password})
    c.run('whoami')

    # Create a responder that will set up the Super User password 
    responder_su = Responder(
        pattern=r'Password:',
        response='root\n',
    )

    # Create a responder that will set up the sudo password 
    responder_su = Responder(
        pattern=r'\[sudo\] password for *:',  # you can specify the username for more security
        response='alarm\n',
    )

    # Run sudo commands
    c.run('sudo whoami', pty=True, watchers=[responder_su])

    # Finally sudo works as expected...
    config = Config(overrides={'sudo': {'password': 'toor'}})
    c = Connection("archnode@192.168.1.243", connect_kwargs={'password':'toor'}, config=config)
    responder_password = Responder(
        pattern=r'\[sudo\] password for *',
        response='toor\n',
    )
    c.sudo("pacman -S base-devel git --noconfirm\n")
    c.run("git clone https://aur.archlinux.org/yay.git\n")
    c.run("cd yay && makepkg -si --noconfirm\n", pty=True, watchers="responder_password")

    # Install docker-machine
    c.run("yay -S docker-machine --noconfirm\n", pty=True, watchers="responder_password")


if __name__ == "__main__":
    print("hello world from main")

    # 1. Connect to raspi first time and run a sample command whomai
    # Connect one raspberry pi
    print("Experiment 1: ")
    raspi1 = RaspiSSH(host="192.168.1.2", port=22, username="alarm", password="alarm")
    raspi1.connect_channel()

    print("Expecting whoami command")
    raspi1.example_command()
    print("Complete!")

    # raspi1.add_root_password("root")
    # 0. Super User setup the keyring
    # 1. install sudo # Use paramiko directly
    # 2. Set Users & groups # Use paramiko directly
    # 3. `Disable` root user
    # 4. Setup yay


