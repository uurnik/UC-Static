import time
import os
from scrapli.driver import GenericDriver
from scrapli.driver.core import JunosDriver ,IOSXEDriver


class AddSSHKeys():
    def __init__(self,device):
        self.driver = None
        self.ip = device['ip']
        self.username = device['username']
        self.password = device['password']


    def get_driver(self):
        conn = GenericDriver(
        host=self.ip,
        auth_username=self.username,
        auth_password=self.password,
        timeout_transport=10,
        timeout_socket=5,
        timeout_ops=10,
        transport="ssh2",
        auth_strict_key=False,
        comms_prompt_pattern=r"^(\w+.*?)([#\s,>\s,#])$",
    )

        conn.open()
        conn.get_prompt()
        output = conn.send_command("show version | inc Cisco").result
        conn.send_command("\n")
        conn.close()

        if "command parse error" in output.lower():
            self.driver =  GenericDriver
        # elif "cisco ios xr" in output.lower():
        #     platform = "iosxr"
        elif "cisco ios xe" in output.lower():
            self.driver =  IOSXEDriver
        elif "cisco ios" in output.lower():
           self.driver =  IOSXEDriver
        else:
            self.driver =  JunosDriver


    def add_key(self):
        driver = self.get_driver()

        with open(f"{os.getcwd()}/ssh_keys/id_rsa.pub") as key_file:
            data = key_file.read()
        
        if driver == GenericDriver or driver == JunosDriver:
            no_line_key = data.replace("\n","")
            key = f'"{no_line_key}"'

            if driver == GenericDriver:
                conn = driver(host=self.ip,auth_username=self.username,transport='ssh2'
                                ,comms_prompt_pattern=r"^.*?\s?#\s",
                                auth_password=self.password,auth_strict_key=False)
                conn.open()
                conn.send_command(f'config system {self.username}')
                conn.send_command(f'edit {self.username}')
                conn.send_command(f'set ssh-public-key1 {key}' )
                conn.send_command("end")
                conn.close()

            elif driver == JunosDriver:
                conn = driver(host=self.ip,auth_username=self.username,transport='ssh2',
                                auth_password=self.password,auth_strict_key=False)
                conn.open()
                conn.send_command(f'edit')
                conn.send_command('edit system login user admin authentication')
                conn.transport.write("set ssh-rsa ")
                time.sleep(0.6)
                conn.transport.write(key)
                time.sleep(0.6)
                conn.transport.write("\n")
                time.sleep(0.6)

                conn.send_command('commit')

                conn.close()


        elif driver == IOSXEDriver:
            key = data.split("\n")
            conn = driver(host=self.ip,auth_username=self.username,transport='ssh2',
                            auth_password=self.password,auth_strict_key=False)
            conn.send_configs(["ip ssh pubkey-chain", "username admin",
                                 "key-string", *key, "exit"])
            
        