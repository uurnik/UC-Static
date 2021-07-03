#!/bin/bash

HEIGHT=15
WIDTH=40
CHOICE_HEIGHT=4
BACKTITLE="Uurnik Connect"
TITLE="Change Configuration"
MENU="Choose one of the following options:"


# Network Manager Connection Profile
CONNECTION_PROFILE="Wired connection 1"


OPTIONS=(1 "Change Hostname"
        2 "Interface Configuration"
        3 "Time Zone"
	    4 "NTP"
        5 "Reboot"
	    6 "Shutdown"
        7 "Password Reset"
        8 "Ping")

INTERFACE_OPTION=(1 "Manual"
                  2 "DHCP")

# First dialog
I=1
while [ $I == 1 ]
do
    CHOICE=$(dialog --clear \
                    --no-cancel \
                    --backtitle "$BACKTITLE" \
                    --title "$TITLE" \
                    --menu "$MENU" \
                    $HEIGHT $WIDTH $CHOICE_HEIGHT \
                    "${OPTIONS[@]}" \
                    2>&1 >/dev/tty)

    clear
    case $CHOICE in
            1)  
                # Changing Hostname 
                clear
                NAME=$(dialog --clear --title "Change Hostname" --backtitle "Configuration" --inputbox "Enter Hostname" $HEIGHT $WIDTH $CHOICE_HEIGHT \
                3>&1 1>&2 2>&3 3>&- )
                echo "$NAME">/etc/hostname
                ;;
            2)
                # Show this menu if Interface configuration is selected
                clear
                INTERFACE_MODE=$(dialog --clear \
                                --backtitle "$BACKTITLE" \
                                --title "Interface Configuration" \
                                --menu "$MENU" \
                                $HEIGHT $WIDTH $CHOICE_HEIGHT \
                                "${INTERFACE_OPTION[@]}" \
                                3>&1 1>&2 2>&3 3>&- )
                clear
                case $INTERFACE_MODE in

                        1)  
                            # If user selected the Manual configuration
                            IP_ADDRESS=$(dialog --clear --title "IP" --backtitle "Configuration" --inputbox "Enter IP ADDRESS" $HEIGHT $WIDTH $CHOICE_HEIGHT \
                                    3>&1 1>&2 2>&3 3>&- )
                            clear
                            GATEWAY=$(dialog --clear --title "Gateway" --backtitle "Configuration" --inputbox "Enter Gateway" $HEIGHT $WIDTH $CHOICE_HEIGHT \
                                    3>&1 1>&2 2>&3 3>&- )
                            clear
                            DNS_1=$(dialog --clear --title "DNS" --backtitle "Configuration" --inputbox "Enter DNS" $HEIGHT $WIDTH $CHOICE_HEIGHT \
                                                3>&1 1>&2 2>&3 3>&- )

                            # Validating configuration paramters
                            IP_RE='(^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$)'
                            IP_ADDRESS_RE='(^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}$)'

                            if [[ "$DNS_1" =~ ${IP_RE} ]] && [[ "$IP_ADDRESS" =~ ${IP_ADDRESS_RE} ]] && [[ "$GATEWAY" =~ ${IP_RE} ]]
                            then

                                nmcli con mod "${CONNECTION_PROFILE}" ipv4.method manual ipv4.address $IP_ADDRESS ipv4.gateway $GATEWAY ipv4.dns $DNS_1
                                RETURN=$?
                                nmcli con down "${CONNECTION_PROFILE}"
                                nmcli con up "${CONNECTION_PROFILE}"
                                clear
                                if [[ "$RETURN" != 0 ]]
                                then
                                    dialog --title "ERROR" --msgbox 'Invalid Parameters' $HEIGHT $WIDTH
                                fi
                            fi
                            ;;
                            
                        2)
                            # if user selected option to use DHCP
                            nmcli con mod "${CONNECTION_PROFILE}" ipv4.method auto
                            nmcli con down "${CONNECTION_PROFILE}"
                            nmcli con up "${CONNECTION_PROFILE}"
                            clear
                            ;;
                esac
                ;;
        3)
            # Changing Time Zone
            clear
            TIME_ZONE=$(dialog --clear --title "Time Zone" --backtitle "Configuration" --inputbox "Enter Time Zone" $HEIGHT $WIDTH $CHOICE_HEIGHT \
                                    3>&1 1>&2 2>&3 3>&- )

            timedatectl set-timezone $TIME_ZONE
            if [[ "$?" != 0 ]]
            then
                dialog --title "ERROR" --msgbox 'Invalid TimeZone' $HEIGHT $WIDTH
            fi
                ;;
        4)
            # configure NTP 
            NTP=$(dialog --clear --title "NTP" --backtitle "Configuration" --inputbox "Enter NTP Server" $HEIGHT $WIDTH $CHOICE_HEIGHT \
                                    3>&1 1>&2 2>&3 3>&-)
            sed -i "s/^#*NTP=.*/NTP=${NTP}/g" /etc/systemd/timesyncd.conf
            systemctl restart systemd-timesyncd
                ;;
        5)
            reboot -f
            ;;
        6)
            shutdown
            ;;
        7)
            PASSWORD=$(dialog --clear --insecure --passwordbox "Enter Password" 15 15 3>&1 1>&2 2>&3 3>&- )
            CONFIRM_PASSWORD=$(dialog --clear --insecure --passwordbox  "Confirm Password" 15 15 3>&1 1>&2 2>&3 3>&- )
            if [[ "$PASSWORD" == "$CONFIRM_PASSWORD" ]]
            then
                yes "$PASSWORD" | sudo passwd $USER
                if [[ "$?" == 0 ]]
                then
                    dialog --title "Success" --msgbox 'Password Changed' $HEIGHT $WIDTH
                else
                    dialog --title "Error" --msgbox 'Error' $HEIGHT $WIDTH
                fi
            else
                dialog --title "Error" --msgbox 'Invalid Password' $HEIGHT $WIDTH
            fi
            ;;
        8)
            # Ping
            IP=$(dialog --clear --title "Ping"  --inputbox "Enter IP" $HEIGHT $WIDTH $CHOICE_HEIGHT \
                            3>&1 1>&2 2>&3 3>&-)
            echo "...."
            OUTPUT=$(ping $IP -c 4 )
            dialog --title "Output" --msgbox "$OUTPUT" 20 50
            ;;
    esac                 
    clear
done 
