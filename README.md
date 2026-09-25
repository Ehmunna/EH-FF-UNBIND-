![logo](Bind.png)
# use termux 
```
pkg update -y
pkg upgrade -y
pkg install python git clang make cmake pkg-config -y
pip install requests urllib3 pycryptodome protobuf==4.25.1
git clone https://github.com/Ehmunna/EH-FF-UNBIND-.git
cd EH-FF-UNBIND-
```
## pip install
```
pip install requests urllib3 pycryptodome protobuf==4.25.1
```
## setup check 
```
python -c "import requests, urllib3; from Crypto.Cipher import AES; import google.protobuf; import MajoRLogin_pb2, MajorLoginRes_pb2; print('ALL MODULES OK')"
```
