"""Sample Power Plant RA/RS status replies used by the tests."""

ZONES = "".join(
    f"&z{n}pwr=0&z{n}name=OUTLET {n}&z{n}dlymode=SW&z{n}tondly=3&z{n}toffdly=3&z{n}priority=1"
    for n in range(1, 17)
)

RA = (
    "&upwr=0&umov=1&ulock=0&uirin=0&uirout=0&utrigin=1&utrigout=1&utdon=3&utdoff=3"
    "&ub=2&ulcd=SSD1963&uflash=SST39VB320&utype=p20&ucur=Hi&uregion=US"
    + ZONES
    + "&voltsin=120.1&voltsout=119.6&thdin=4.5&thdout=0.2&amps=0.01&watts=5&freq=60.0"
    "&dc=15&temp1=23&temp2=27&waveform=sine&mwstrength=4&voltssetting=120&regmode=reg"
    "&buckena=no&boostena=yes&buckboostact=no&phasetune=0&dhcps=0&dhcp=1"
    "&mac=001122334455&ip=10.0.0.50&mask=255.255.255.0&gateway=10.0.0.1"
    "&pdns=10.0.0.1&sdns=0.0.0.0&hostname=POWERPLANT&fwvproc=0.01.25"
    "&fwvboot=1.13.00&fwvweb=1.22.00&fwvmtr=0.21.00&fwvosc=0.57.00"
)

RS = (
    "&upwr=0&umov=1&zpwr=0000000000000000&voltsin=120.2&voltsout=119.6&thdin=4.5"
    "&thdout=0.2&watts=5&waveform=sine&voltssetting=120&regmode=reg"
)

HOST = "10.0.0.50"
MAC = "00:11:22:33:44:55"
