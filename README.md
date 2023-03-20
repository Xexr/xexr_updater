# xexr_updater
A python script to detect changes in your mullvad vpn connection and update and restart an ethereum execution and consensus client if your vpn exit ip changes. This is currently setup for the Besu EC and the Nimbus CC, but you can easily edit the relevant constants to make it work with another EC / CC combination.

Instructions for an example ubuntu node are shown below:

1. Update the constants to point to your EC / CC (updating the IP_STR & Patterns as appropriate for your clients systemctl service file)
2. Create a user that will run the script, e.g. "xexr_updater"
3. Add the user to a group, e.g. ethereum_users and allow that group to edit your EC / CC service files
4. Add the user to your sudoers file, allowing it to run systemctl daemon-reload and the restart commands for your EC / CC
5. Copy the xexr_updater.service file to your /etc/systemd/system folder, and edit the paths as appropriate to point to wherever you save the main xexr_updater.py script
6. Make sure the owner of the xexr_updater script is your newly created user
7. Run "sudo systemctl start xexr_updater" to start the script
8. Check it's running correctly with "journalctl -fu xexr_updater"
9. Enable it at boot with "sudo systemctl enable xexr_updater"
