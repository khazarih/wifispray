# wifispray

A simple tool for wifi password spraying. (Tester on Fedora 39).

<br/>
<br/>

Environment setup (optional, you can also install packages globally).
```bash
git clone https://github.com/khazarih/wifispray.git
cd wifispray
python3 -m venv wifispray-env
source wifispray-env/bin/activate
pip install -r requirements.txt
```

<br/>


Usage without waiting for results. The system should automatically connect if there was any successful login.

```bash
sudo ./wifispray-env/bin/python wifispray.py -i wlan0 -p p@ssw0rd1234
```

<br/>


You can also use -w/--wait for waiting results but it will take longer.

```bash
sudo ./wifispray-env/bin/python wifispray.py -i wlan0 -p p@ssw0rd1234 -w
```