$ORIGIN .
$TTL 604800     ; 1 week
uurnikconnect.com       IN SOA  uurnik.uurnikconnect.com. root.uurnik.uurnikconnect.com. (
                                9          ; serial
                                604800     ; refresh (1 week)
                                86400      ; retry (1 day)
                                2419200    ; expire (4 weeks)
                                604800     ; minimum (1 week)
                                )
                        NS      uurnik.uurnikconnect.com.
                        AAAA    ::1
$ORIGIN uurnikconnect.com.
$TTL 300        ; 5 minutes
uurnik                 A       127.0.0.1
