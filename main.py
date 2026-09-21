import requests
import os
import sys
import json
import time
import urllib.parse
import base64
import hashlib
import urllib3
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
except ImportError:
    print("\n\033[91m [!] Error: Protobuf files (MajoRLogin_pb2.py, MajorLoginRes_pb2.py) not found in directory!\033[0m")
    sys.exit()


class Colors:
    HEADER   = '\033[95m'
    BLUE     = '\033[94m'
    CYAN     = '\033[96m'
    GREEN    = '\033[92m'
    YELLOW   = '\033[93m'
    RED      = '\033[91m'
    MAGENTA  = '\033[95m'
    WHITE    = '\033[97m'
    BOLD     = '\033[1m'
    DIM      = '\033[2m'
    END      = '\033[0m'
    ITALIC   = '\033[3m'
    UNDERLINE= '\033[4m'
    BG_BLACK = '\033[40m'
    ORANGE   = '\033[38;5;208m'
    PINK     = '\033[38;5;213m'
    LBLUE    = '\033[38;5;75m'
    TEAL     = '\033[38;5;43m'
    GOLD     = '\033[38;5;220m'
    GRAY     = '\033[38;5;245m'
    DBLUE    = '\033[38;5;27m'


# ── slim line helpers ────────────────────────────────
def _line(ch='─', color=None):
    c = color or Colors.DBLUE
    return f"{c}{ch * 46}{Colors.END}"

def _section(title, color=None):
    c = color or Colors.GOLD
    return f"\n {Colors.DBLUE}┌─{Colors.END} {c}{Colors.BOLD}{title}{Colors.END}"

def _kv(key, val, kc=None, vc=None):
    kc = kc or Colors.TEAL
    vc = vc or Colors.WHITE
    return f" {Colors.DBLUE}│{Colors.END}  {kc}{key:<12}{Colors.END}  {vc}{val}{Colors.END}"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_header(subtitle=""):
    clear_screen()

    logo = [
        f"{Colors.GREEN}███████╗██╗  ██╗  ██████╗ ██╗███╗  ██╗██████╗{Colors.END}",
        f"{Colors.GREEN}██╔════╝██║  ██║  ██╔══██╗██║████╗ ██║██╔══██╗{Colors.END}",
        f"{Colors.GREEN}█████╗  ███████║  ██████╔╝██║██╔██╗██║██║  ██║{Colors.END}",
        f"{Colors.GREEN}██╔══╝  ██╔══██║  ██╔══██╗██║██║╚████║██║  ██║{Colors.END}",
        f"{Colors.GREEN}███████╗██║  ██║  ██████╔╝██║██║ ╚███║██████╔╝{Colors.END}",
        f"{Colors.GREEN}╚══════╝╚═╝  ╚═╝  ╚═════╝ ╚═╝╚═╝  ╚══╝╚═════╝{Colors.END}",
    ]
    print()
    for l in logo:
        print(f" {l}")

    now = datetime.now().strftime("%d %b %Y  %H:%M")
    print()
    print(f" {Colors.DBLUE}{'─' * 46}{Colors.END}")
    print(f" {Colors.GOLD}{Colors.BOLD}EH BIND{Colors.END}  "
          f"{Colors.GRAY}v2.0{Colors.END}  "
          f"{Colors.DBLUE}│{Colors.END}  "
          f"{Colors.TEAL}EH MUNNA{Colors.END}  "
          f"{Colors.DBLUE}│{Colors.END}  "
          f"{Colors.GRAY}{now}{Colors.END}")
    print(f" {Colors.DBLUE}{'─' * 46}{Colors.END}")

    if subtitle:
        print(f" {Colors.GOLD}▶ {Colors.BOLD}{subtitle}{Colors.END}")
        print(f" {Colors.DBLUE}{'─' * 46}{Colors.END}")
    print()

def input_prompt(msg):
    print(f" {Colors.DBLUE}┌ {Colors.GOLD}{Colors.BOLD}{msg}{Colors.END}")
    val = input(f" {Colors.DBLUE}└▶ {Colors.WHITE}").strip()
    print(Colors.END, end="")
    return val

def print_step(current, total, msg):
    done = '█' * current
    left = '░' * (total - current)
    print(f"\n {Colors.TEAL}{done}{Colors.GRAY}{left}{Colors.END}  "
          f"{Colors.GOLD}{Colors.BOLD}[{current}/{total}]{Colors.END}  "
          f"{Colors.WHITE}{msg}{Colors.END}")

def print_success(msg):
    print(f" {Colors.GREEN}✔  {msg}{Colors.END}")

def print_error(msg):
    print(f" {Colors.RED}✘  {msg}{Colors.END}")

def print_info(msg):
    print(f" {Colors.LBLUE}◈  {msg}{Colors.END}")

def print_banner(title):
    print(f"\n {Colors.DBLUE}{'─' * 46}{Colors.END}")
    print(f" {Colors.GOLD}{Colors.BOLD}{title}{Colors.END}")
    print(f" {Colors.DBLUE}{'─' * 46}{Colors.END}\n")

def wait_for_enter():
    print(f"\n {Colors.DBLUE}{'─' * 46}{Colors.END}")
    input(f" {Colors.GRAY}Press {Colors.WHITE}Enter{Colors.GRAY} to return …{Colors.END}  ")
    print(Colors.END, end="")


def format_response(response_text, title="API Response"):
    try:
        parsed = json.loads(response_text)
        result_code = parsed.get("result")
        
        if result_code == 0:
            print_success(f"{title}: SUCCESS")
        elif result_code is not None:
            error_msg = parsed.get("error", "Unknown error")
            print_error(f"{title}: FAILED (Code: {result_code} | {error_msg})")
        else:
            print_info(f"{title}: Completed (No standard result code)")
            
    except Exception:
        if '"result": 0' in response_text.replace(" ", ""):
            print_success(f"{title}: SUCCESS")
        else:
            print_error(f"{title}: Unrecognized response format")


def convert_seconds(s):
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"


PLATFORM_MAP = {
    1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK", 
    6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line", 
    11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"
}

def check_bind_info(access_token=None, show_raw=False):
    if not access_token:
        access_token = input_prompt("Enter Access Token")
    
    print_info("Fetching account bind information from Garena...\n")
    

    try:
        player_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        player_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }

        p_res = requests.get(player_url, headers=player_headers, timeout=15, allow_redirects=True)
        
        parsed_url = urllib.parse.urlparse(p_res.url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        uid = query_params.get("account_id", ["Unknown"])[0]
        nickname = query_params.get("nickname", ["Unknown"])[0]
        region = query_params.get("region", ["Unknown"])[0]
        
        print(f"  {Colors.GREEN}{Colors.BOLD}≡ Player Information{Colors.END}")
        print(f"    {Colors.CYAN}● UID:{Colors.END}       {Colors.WHITE}{uid}{Colors.END}")
        print(f"    {Colors.YELLOW}● Nickname:{Colors.END}  {Colors.WHITE}{nickname}{Colors.END}")
        print(f"    {Colors.MAGENTA}● Region:{Colors.END}    {Colors.WHITE}{region}{Colors.END}\n")
        
    except Exception as e:
        print_error(f"Failed to fetch player details: {str(e)}\n")


    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    payload = {'app_id': "100067", 'access_token': access_token}
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    
    try:
        response = requests.get(url, params=payload, headers=headers, timeout=15)
        
        print(f"  {Colors.GREEN}{Colors.BOLD}≡ Bind Information{Colors.END}")
        
        if response.status_code == 200:
            data = response.json()
            
            email = data.get("email", "")
            email_to_be = data.get("email_to_be", "")
            countdown = data.get("request_exec_countdown", 0)
            
            countdown_human = convert_seconds(countdown)
            result_code = data.get("result", -1)
            
            print(f"    {Colors.CYAN}● Current Email:{Colors.END}  {Colors.WHITE}{email if email else 'None'}{Colors.END}")
            print(f"    {Colors.YELLOW}● Pending Email:{Colors.END}  {Colors.WHITE}{email_to_be if email_to_be else 'None'}{Colors.END}")
            if email_to_be:
                print(f"    {Colors.MAGENTA}● Countdown:{Colors.END}      {Colors.WHITE}{countdown_human}{Colors.END}")
            if result_code == 0:
                print(f"    {Colors.GREEN}● Result:{Colors.END}         {Colors.GREEN}✓ SUCCESS{Colors.END}")
            else:
                print(f"    {Colors.RED}● Result:{Colors.END}         {Colors.RED}✗ FAILED (Code: {result_code}){Colors.END}")

            summary = ""
            if email == "" and email_to_be != "":
                summary = f"Pending email confirmation: {email_to_be} - Confirms in: {countdown_human}"
            elif email != "" and email_to_be == "":
                summary = f"Email confirmed: {email}"
            elif email == "" and email_to_be == "":
                summary = "No recovery email set"
                
            if summary:
                print(f"\n    {Colors.BLUE}● Summary:{Colors.END} {Colors.WHITE}{summary}{Colors.END}")

            if show_raw:
                print(f"\n    {Colors.DIM}Raw Response: {json.dumps(data)}{Colors.END}")
                
        else:
            print_error(f"API Error (Status {response.status_code}): {response.text[:100]}")
            
    except Exception as e:
        print_error(f"Failed to fetch info: {str(e)}")


def bind_email():
    draw_header("BIND EMAIL")
    
    access_token = input_prompt("Enter Access Token")
    print("")
    check_bind_info(access_token, show_raw=False)
    print("")
    email = input_prompt("Enter Email to bind")
    
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    print_step(1, 3, f"Sending OTP to {email}...")
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    send_otp_data = {
        "email": email,
        "locale": "en_PK",
        "region": "PK",
        "app_id": "100067",
        "access_token": access_token
    }
    resp_send = requests.post(send_otp_url, headers=headers, data=send_otp_data)
    format_response(resp_send.text, "Send OTP")

    otp = input_prompt("Enter OTP received in email")

    print_step(2, 3, "Verifying OTP securely...")
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    verify_data = {
        "app_id": "100067",
        "access_token": access_token,
        "email": email,
        "code": otp,
        "otp": otp,
        "type": "1"
    }
    resp_verify = requests.post(verify_url, headers=headers, data=verify_data)
    format_response(resp_verify.text, "Verify OTP")

    verifier_token = ""
    try:
        verifier_token = resp_verify.json().get("verifier_token", "")
    except: pass

    if not verifier_token:
        print_error("Could not automatically extract verifier_token.")
        verifier_token = input_prompt("Please enter the verifier_token manually")
    else:
        print_success("Verifier Token extracted successfully!")

    security_code = input_prompt("Set 6-digits security code")

    print_step(3, 3, "Creating bind request...")
    bind_url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
    bind_data = {
        "email": email,
        "app_id": "100067",
        "access_token": access_token,
        "verifier_token": verifier_token,
        "secondary_password": security_code
    }
    resp_bind = requests.post(bind_url, headers=headers, data=bind_data)
    format_response(resp_bind.text, "Final Bind Request")

    wait_for_enter()


def change_bind_email():
    draw_header("CHANGE BIND EMAIL")
    
    print(f" {Colors.CYAN}CHOOSE CHANGE METHOD:{Colors.END}")
    print(f" {Colors.MAGENTA}⊛ [{Colors.WHITE}1{Colors.MAGENTA}] {Colors.WHITE}CHANGE VIA OTP{Colors.END}")
    print(f" {Colors.MAGENTA}⊛ [{Colors.WHITE}2{Colors.MAGENTA}] {Colors.WHITE}CHANGE VIA SECURITY CODE{Colors.END}")
    print(f" {Colors.MAGENTA}⊛ {Colors.RED}[0] CANCEL & GO BACK{Colors.END}\n")
    
    choice = input_prompt("Select Method")
    if choice == "0":
        return
    if choice not in ["1", "2"]:
        print_error("Invalid option selected!")
        return wait_for_enter()

    access_token = input_prompt("Enter Access Token")
    print("")
    check_bind_info(access_token, show_raw=False)
    
    try:
        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        info_payload = {'app_id': "100067", 'access_token': access_token}
        info_headers = {'User-Agent': "GarenaMSDK/4.0.30"}
        r_info = requests.get(url_info, params=info_payload, headers=info_headers, timeout=10)
        old_email = r_info.json().get("email", "")
    except:
        old_email = ""
        
    if not old_email:
        print_error("No currently bound email found! You cannot use 'Change Bind' without an existing email.")
        return wait_for_enter()
    
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    identity_token = None
    total_steps = 5 if choice == "1" else 4
    current_step = 1

    if choice == "1":
        print_step(current_step, total_steps, f"Sending OTP to {old_email}...")
        url_send = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        data = {"email": old_email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": access_token}
        r = requests.post(url_send, headers=headers, data=data)
        format_response(r.text, "Send Old Email OTP")
        current_step += 1
            
        otp_old = input_prompt(f"Enter OTP from {old_email}")
            
        print_step(current_step, total_steps, "Verifying Old Email Identity...")
        url_verify_identity = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        data = {"email": old_email, "app_id": "100067", "access_token": access_token, "otp": otp_old}
        r = requests.post(url_verify_identity, headers=headers, data=data)
        format_response(r.text, "Verify Identity")
        current_step += 1
        
        try: identity_token = r.json().get("identity_token")
        except: pass

    else:
        sec_code = input_prompt("Enter 6-digit Security Code")
        
        hashed_sec_code = hashlib.sha256(sec_code.encode('utf-8')).hexdigest()
        
        print_step(current_step, total_steps, "Verifying Identity via Security Code...")
        url_verify_identity = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        data = {"email": old_email, "app_id": "100067", "access_token": access_token, "secondary_password": hashed_sec_code}
        r = requests.post(url_verify_identity, headers=headers, data=data)
        format_response(r.text, "Verify Identity")
        current_step += 1
        
        try: identity_token = r.json().get("identity_token")
        except: pass

    if identity_token:
        print_success("Identity Token Extracted!")
    else:
        print_error("No identity token received or verification failed!")
        return wait_for_enter()

    new_email = input_prompt("Enter New Email")

    print_step(current_step, total_steps, f"Sending OTP to {new_email}...")
    url_send = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email": new_email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": access_token}
    r = requests.post(url_send, headers=headers, data=data)
    format_response(r.text, "Send New Email OTP")
    current_step += 1
    
    otp_new = input_prompt(f"Enter OTP from {new_email}")

    print_step(current_step, total_steps, "Verifying New Email OTP...")
    url_verify_otp = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {"email": new_email, "app_id": "100067", "access_token": access_token, "otp": otp_new}
    r = requests.post(url_verify_otp, headers=headers, data=data)
    format_response(r.text, "Verify OTP")
    current_step += 1

    verifier_token = None
    try:
        verifier_token = r.json().get("verifier_token")
        if verifier_token:
            print_success("Verifier Token Extracted!")
        else:
            print_error("No verifier token received!")
            return wait_for_enter()
    except:
        return wait_for_enter()

    print_step(current_step, total_steps, "Creating Rebind Request...")
    url_rebind = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
    data = {"identity_token": identity_token, "email": new_email, "app_id": "100067", "verifier_token": verifier_token, "access_token": access_token}
    r = requests.post(url_rebind, headers=headers, data=data)
    format_response(r.text, "Rebind Request")

    wait_for_enter()


def unbind_email():
    draw_header("UNBIND EMAIL")
    
    print(f" {Colors.CYAN}CHOOSE UNBIND METHOD:{Colors.END}")
    print(f" {Colors.MAGENTA}⊛ [{Colors.WHITE}1{Colors.MAGENTA}] {Colors.WHITE}UNBIND VIA OTP{Colors.END}")
    print(f" {Colors.MAGENTA}⊛ [{Colors.WHITE}2{Colors.MAGENTA}] {Colors.WHITE}UNBIND VIA SECURITY CODE{Colors.END}")
    print(f" {Colors.MAGENTA}⊛ {Colors.RED}[0] CANCEL & GO BACK{Colors.END}\n")
    
    choice = input_prompt("Select Method")
    if choice == "0":
        return
    if choice not in ["1", "2"]:
        print_error("Invalid option selected!")
        return wait_for_enter()

    access_token = input_prompt("Enter Access Token")
    print("")
    check_bind_info(access_token, show_raw=False)
    

    try:
        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        info_payload = {'app_id': "100067", 'access_token': access_token}
        info_headers = {'User-Agent': "GarenaMSDK/4.0.30"}
        r_info = requests.get(url_info, params=info_payload, headers=info_headers, timeout=10)
        email = r_info.json().get("email", "")
    except:
        email = ""
        
    if not email:
        print_error("No currently bound email found! You cannot use 'Unbind' without an existing email.")
        return wait_for_enter()
    
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    identity_token = None

    if choice == "1":
        print_step(1, 3, f"Sending OTP to {email}...")
        send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        send_otp_data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": access_token}
        resp = requests.post(send_otp_url, headers=headers, data=send_otp_data)
        format_response(resp.text, "Send OTP")
        
        otp = input_prompt(f"Enter OTP from {email}")
        
        print_step(2, 3, "Verifying Identity...")
        verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        verify_data = {"email": email, "app_id": "100067", "access_token": access_token, "otp": otp}
        resp = requests.post(verify_url, headers=headers, data=verify_data)
        format_response(resp.text, "Verify Identity")
        
        try: identity_token = resp.json().get("identity_token")
        except: pass
        step_final = 3

    else:
        sec_code = input_prompt("Enter 6-digit Security Code")
        
        hashed_sec_code = hashlib.sha256(sec_code.encode('utf-8')).hexdigest()
        
        print_step(1, 2, "Verifying Identity via Security Code...")
        verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        verify_data = {"email": email, "app_id": "100067", "access_token": access_token, "secondary_password": hashed_sec_code}
        resp = requests.post(verify_url, headers=headers, data=verify_data)
        format_response(resp.text, "Verify Identity")
        
        try: identity_token = resp.json().get("identity_token")
        except: pass
        step_final = 2

    if identity_token:
        print_success("Identity Token Extracted!")
    else:
        print_error("Identity verification failed!")
        return wait_for_enter()

    total_steps = 3 if choice == "1" else 2
    print_step(step_final, total_steps, "Creating Unbind Request...")
    unbind_url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
    unbind_data = {"app_id": "100067", "access_token": access_token, "identity_token": identity_token}
    resp = requests.post(unbind_url, headers=headers, data=unbind_data)
    format_response(resp.text, "Unbind Request")
    
    wait_for_enter()


def cancel_bind():
    draw_header("CANCEL BIND REQUEST")
    
    access_token = input_prompt("Enter Access Token")
    print("")
    check_bind_info(access_token, show_raw=False)
    
    print_step(1, 1, "Creating Cancel Request...")
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {"app_id": "100067", "access_token": access_token}
    response = requests.post(url, headers=headers, data=data)
    
    format_response(response.text, "Cancel Request")
    wait_for_enter()



def bind_info():
    draw_header("CHECK BIND INFO")
    access_token = input_prompt("Enter Access Token")
    print("")
    check_bind_info(access_token, show_raw=False)
    wait_for_enter()


def eat_to_access_token():
    draw_header("EAT TO ACCESS TOKEN")
    
    user_input = input_prompt("Enter EAT Token OR Full EAT URL")
    
    eat_token = None
    if "http" in user_input or "?" in user_input:
        parsed_url = urllib.parse.urlparse(user_input)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        if 'eat' in query_params:
            eat_token = query_params['eat'][0]
    else:
        eat_token = user_input.strip()
        
    if not eat_token:
        print_error("Could not find an EAT token in your input.")
        return wait_for_enter()
        
    print_step(1, 1, "Contacting Server & Following Redirects...")
    
    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
    }
    
    try:
        response = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed_final = urllib.parse.urlparse(response.url)
        final_params = urllib.parse.parse_qs(parsed_final.query)
        
        if 'access_token' in final_params:
            access_token = final_params['access_token'][0]
            account_id = final_params.get('account_id', ['Unknown'])[0]
            nickname = final_params.get('nickname', ['Unknown'])[0]
            region = final_params.get('region', ['Unknown'])[0]
            

            print(f"\n\033[92m●{'═' * 19} \033[97m\033[1mSUCCESS\033[0m \033[92m{'═' * 20}●\033[0m")
            print(f" \033[96mNickname    :\033[0m \033[97m{urllib.parse.unquote(nickname)}\033[0m")
            print(f" \033[96mAccount ID  :\033[0m \033[97m{account_id}\033[0m")
            print(f" \033[96mRegion      :\033[0m \033[97m{region}\033[0m")
            print(f" \033[96mAccess Token:\033[0m\n \033[93m{access_token}\033[0m")
            print(f"\033[92m●{'═' * 48}●\033[0m")
            
        else:
            print_error("Access token not found. The token might be expired or invalid.")
            
    except Exception as e:
        print_error(f"Failed to generate access token: {str(e)}")
        
    wait_for_enter()


def revoke_access_token():
    draw_header("REVOKE ACCESS TOKEN")
    
    access_token = input_prompt("Enter Access Token to Revoke")
    if not access_token:
        print_error("Token cannot be empty.")
        return wait_for_enter()
        
    print_step(1, 2, "Checking Token Status & Fetching Info...")
    
    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    nickname = "Unknown"
    account_id = "Unknown"
    region = "Unknown"
    is_valid = False
    
    try:
        res = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed = urllib.parse.urlparse(res.url)
        params = urllib.parse.parse_qs(parsed.query)
        
        if 'access_token' in params:
            is_valid = True
            nickname = urllib.parse.unquote(params.get('nickname', ['Unknown'])[0])
            account_id = params.get('account_id', ['Unknown'])[0]
            region = params.get('region', ['Unknown'])[0]
    except Exception:
        pass
        
    if not is_valid:
        print_error("Token is already invalid, expired, or revoked!")
        return wait_for_enter()
        
    print_success(f"Token is Valid!")
    
    print_step(2, 2, "Revoking Token Access (Logging Out)...")
    
    refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
    logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh_token}"
    
    try:
        logout_res = requests.get(logout_url, headers=headers, timeout=15)
        
        if logout_res.status_code == 200 and "error" not in logout_res.text:

            print(f"\n\033[92m●{'═' * 19} \033[97m\033[1mREVOKED\033[0m \033[92m{'═' * 20}●\033[0m")
            print(f" \033[96mNickname    :\033[0m \033[97m{nickname}\033[0m")
            print(f" \033[96mAccount ID  :\033[0m \033[97m{account_id}\033[0m")
            print(f" \033[96mRegion      :\033[0m \033[97m{region}\033[0m")
            print(f" \033[96mStatus      :\033[0m \033[92mSuccessfully Logged Out & Revoked\033[0m")
            print(f"\033[92m●{'═' * 48}●\033[0m\n")
        else:
            print_error("Failed to revoke token! Server responded with an error.")
            
    except Exception as e:
        print_error(f"Error while revoking token: {str(e)}")
        
    wait_for_enter()


def access_to_jwt():
    draw_header("ACCESS TOKEN TO JWT")
    
    token = input_prompt("Enter Access Token")
    if not token:
        print_error("Empty Input! Token cannot be blank.")
        return wait_for_enter()
        
    print_step(1, 1, "Connecting to Vercel API Server...")
    
    url = f"https://acesstojwt-sigma.vercel.app/token?access_token={token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            raw_text = response.text.strip()
            jwt_token = None
            
            try:
                data = json.loads(raw_text)
                if isinstance(data, dict) and "token" in data:
                    jwt_token = data["token"]
            except Exception:
                jwt_token = raw_text

            if jwt_token and (jwt_token.startswith("ey") or len(jwt_token) > 20):
                print("\n" + f"\033[92m●{'═' * 16} \033[97m\033[1mJWT GENERATED\033[0m \033[92m{'═' * 17}●\033[0m\n")
                print(f" {Colors.GREEN}⊛ Game JWT Token:{Colors.END}\n")
                print(f" \033[1;92m{jwt_token}\033[0m\n")
                print(f"\033[92m●{'═' * 48}●\033[0m")
            else:
                print_error("Invalid response or token format received from server.")
                print(f" {Colors.DIM}Raw Response: {raw_text[:100]}{Colors.END}")
        else:
            print_error(f"Server Error! HTTP Status Code: {response.status_code}")
            
    except Exception as e:
        print_error(f"Connection Failed: {str(e)}")
        
    wait_for_enter()


def ban_account():
    draw_header("BAN ACCOUNT (ACCESS TOKEN TO BAN)")
    
    token = input_prompt("Enter Access Token")
    if not token:
        print_error("Empty Input! Token cannot be blank.")
        return wait_for_enter()
        
    print_step(1, 1, "Sending Ban Request to API Server...")
    
    url = f"https://toji-api-jwt.vercel.app/ban?token={token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        print("\n" + f"\033[92m●{'═' * 16} \033[97m\033[1mAPI RESPONSE\033[0m \033[92m{'═' * 17}●\033[0m\n")
        
        if response.status_code == 200:
            raw_text = response.text.strip()
            try:
                parsed_json = json.loads(raw_text)
                print(f"{Colors.GREEN} ⊛ Raw JSON Response:{Colors.END}")
                print(f" {Colors.WHITE}{json.dumps(parsed_json, indent=4)}{Colors.END}")
            except Exception:
                print(f" {Colors.WHITE}{raw_text}{Colors.END}")
        else:
            print_error(f"Server Alert! HTTP Status Code: {response.status_code}")
            print(f" {Colors.DIM}Response: {response.text}{Colors.END}")
            
        print(f"\n\033[92m●{'═' * 48}●\033[0m")
    except Exception as e:
        print_error(f"Connection Failed: {str(e)}")
        
    wait_for_enter()


AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'

def enc(d): return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))
def dec(d): return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

def build_majorlogin(tok, open_id, p_type):
    m = mLpB.MajorLogin()
    m.event_time = str(datetime.now())[:-7]
    m.game_name = "free fire"
    m.platform_id = p_type
    m.client_version = "1.120.1"
    m.system_software = "Android OS 9 / API-28"
    m.system_hardware = "Handheld"
    m.telecom_operator = "Verizon"
    m.network_type = "WIFI"
    m.screen_width = 1920
    m.screen_height = 1080
    m.screen_dpi = "280"
    m.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    m.memory = 3003
    m.gpu_renderer = "Adreno (TM) 640"
    m.gpu_version = "OpenGL ES 3.1 v1.46"
    m.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    m.client_ip = "223.191.51.89"
    m.language = "en"
    m.open_id = open_id
    m.open_id_type = str(p_type)
    m.device_type = "Handheld"
    m.access_token = tok
    m.platform_sdk_id = 1
    m.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    m.login_by = 3
    m.channel_type = 3
    m.cpu_type = 2
    m.cpu_architecture = "64"
    m.client_version_code = "2019118695"
    m.login_open_id_type = p_type
    m.origin_platform_type = str(p_type)
    m.primary_platform_type = str(p_type)
    return enc(m.SerializeToString())

def read_varint(data, offset):
    res = 0; shift = 0
    while True:
        if offset >= len(data): break
        b = data[offset]; offset += 1
        res |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return res, offset

def parse_record(data):
    rec = {}; offset = 0
    while offset < len(data):
        tag, offset = read_varint(data, offset)
        wt, f = tag & 7, tag >> 3
        if wt == 0:
            val, offset = read_varint(data, offset)
            if f == 1: rec['ts'] = val
            elif f == 2: rec['ram'] = val
        elif wt == 2:
            length, offset = read_varint(data, offset)
            val = data[offset:offset+length]; offset += length
            if f == 3: rec['dev'] = val.decode(errors='ignore')
            elif f == 4: rec['arch'] = val.decode(errors='ignore')
        else: break
    return rec

def parse_history_protobuf(data):
    records = []; offset = 0
    while offset < len(data):
        tag, offset = read_varint(data, offset)
        wt, f = tag & 7, tag >> 3
        if wt == 0: val, offset = read_varint(data, offset)
        elif wt == 2:
            length, offset = read_varint(data, offset)
            val = data[offset:offset+length]; offset += length
            if f == 1: records.append(parse_record(val))
        else: break
    return records

def login_history():
    draw_header("GET LOGIN HISTORY")
    
    token = input_prompt("Enter Access Token OR Game JWT Token")
    if not token:
        print_error("Empty Input! Token cannot be blank.")
        return wait_for_enter()
        
    jwt_token = None
    
    if token.startswith("ey") and "." in token:
        jwt_token = token
        print_success("Detected valid JWT Token.")
    else:
        print_step(1, 2, "Resolving Open ID from Access Token...")
        oId = None
        
        try:
            r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={token}", headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
            oId = r.get("open_id")
        except: pass

        if not oId:
            try:
                uid_headers = {"access-token": token, "user-agent": "Mozilla/5.0"}
                uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/", headers=uid_headers, verify=False, timeout=5).json()
                uid = uid_res.get("uid")
                if uid:
                    openid_res = requests.post("https://topup.pk/api/auth/player_id_login", json={"app_id": 100067, "login_id": str(uid)}, verify=False, timeout=5).json()
                    oId = openid_res.get("open_id")
            except: pass

        if not oId:
            print_error("Failed to extract Open ID. Token is likely invalid or expired.")
            return wait_for_enter()
            
        print_success(f"Open ID Extracted: {oId}")
        print_step(2, 2, "Bypassing MajorLogin via Protobufs...")
        
        platforms = [8, 3, 4, 6] 
        for p_type in platforms:
            pl = build_majorlogin(token, oId, p_type)
            try:
                mLhDr  = {
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-S908E Build/TP1A.220624.014)",
                    "Connection": "Keep-Alive", "Accept-Encoding": "gzip",
                    "Content-Type": "application/octet-stream", "Expect": "100-continue",
                    "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1", "ReleaseVersion": "OB52"
                }
                x = requests.post("https://loginbp.ggpolarbear.com/MajorLogin", headers=mLhDr, data=pl, timeout=10, verify=False)
                if x.status_code == 200:
                    res = mLrPb.MajorLoginRes()
                    try: res.ParseFromString(dec(x.content))
                    except: res.ParseFromString(x.content)
                    if res.token:
                        jwt_token = res.token
                        print_success(f"JWT Token Generated Successfully via Platform ID {p_type}!")
                        break
            except: continue
            
        if not jwt_token:
            print_error("MajorLogin failed across all platforms. Token might be blocked.")
            return wait_for_enter()

    try:
        payload_b64 = jwt_token.split('.')[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        
        name = urllib.parse.unquote(decoded.get("nickname", "Unknown"))
        uid = decoded.get("account_id", "Unknown")
        region = decoded.get("lock_region", "Unknown")
        p_id = decoded.get("external_type", 0)
        platform = PLATFORM_MAP.get(p_id, f"Unknown ({p_id})")
        
        print(f"\n\033[92m●{'═' * 17} \033[97m\033[1mPLAYER INFO\033[0m \033[92m{'═' * 18}●\033[0m")
        print(f" \033[96mAccount Name:\033[0m \033[97m{name}\033[0m")
        print(f" \033[96mAccount ID  :\033[0m \033[97m{uid}\033[0m")
        print(f" \033[96mPlatform    :\033[0m \033[97m{platform}\033[0m")
        print(f" \033[96mRegion      :\033[0m \033[97m{region}\033[0m")
        print(f"\033[92m●{'═' * 48}●\033[0m")
    except:
        pass

    print("")
    print_info("Fetching Login History Records...")
    print("")
    hH = {
        "Expect": "100-continue", "Authorization": f"Bearer {jwt_token}",
        "X-Unity-Version": "2018.4.11f1", "X-GA": "v1 1", "ReleaseVersion": "OB52",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; G011A Build/PI)",
        "Host": "client.ind.freefiremobile.com", "Connection": "close"
    }
    
    try:
        r = requests.post("https://client.ind.freefiremobile.com/GetLoginHistory", headers=hH, data=enc(b""), timeout=15, verify=False)
        if r.status_code != 200:
            print_error(f"History Request Failed: HTTP {r.status_code}")
            return wait_for_enter()
            
        try: d = dec(r.content)
        except: d = r.content
        
        records = parse_history_protobuf(d)
        
        print(f"\033[95m●{'═' * 16} \033[97m\033[1mLOGIN HISTORY\033[0m \033[95m{'═' * 17}●\033[0m\n")
        
        if not records:
            print(f" \033[93m⊛ No login history records found for this account.\033[0m")
        else:
            for i, rec in enumerate(records, 1):
                ts_raw = rec.get('ts', 0)
                try: date_str = datetime.fromtimestamp(ts_raw).strftime('%Y-%m-%d %H:%M:%S')
                except: date_str = "Invalid Format"

                dev = rec.get('dev', 'Unknown Device')
                arch = rec.get('arch', 'Unknown Architecture')
                ram = rec.get('ram', 0)

                print(f" \033[92m⊛ Record #{i}\033[0m")
                print(f"   \033[96m● Timestamp/ID :\033[0m \033[97m{ts_raw}\033[0m")
                print(f"   \033[96m● Last Login   :\033[0m \033[97m{date_str}\033[0m")
                print(f"   \033[96m● Device       :\033[0m \033[97m{dev}\033[0m")
                print(f"   \033[96m● Architecture :\033[0m \033[97m{arch}\033[0m")
                print(f"   \033[96m● Memory (RAM) :\033[0m \033[97m{ram} MB\033[0m\n")
                
        print(f"\033[95m●{'═' * 48}●\033[0m")
        
    except Exception as e:
        print_error(f"Connection or Decoding Error: {str(e)}")

    wait_for_enter()


def check_bound_accounts():
    draw_header("PLATFORM BIND INFO")
    
    access_token = input_prompt("Enter Access Token")
    if not access_token:
        print_error("Token cannot be blank.")
        return wait_for_enter()
        
    print("")
    print_info("Fetching platform bind data from Garena Server...")
    print("")
    
    url = "https://100067.connect.garena.com/bind/app/platform/info/get"
    params = {"access_token": access_token}
    headers = {
        "User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print_error(f"Failed to fetch data (HTTP {response.status_code})")
            return wait_for_enter()
            
        d = response.json()
        
        bounded_accounts = d.get("bounded_accounts", [])
        available_platforms = d.get("available_platforms", [])
                
        print(f"{Colors.MAGENTA}●{'═' * 16} {Colors.WHITE}{Colors.BOLD}PLATFORM BINDS{Colors.END} {Colors.MAGENTA}{'═' * 16}●{Colors.END}\n")
        
        print(f" {Colors.GREEN}⊛ BOUND ACCOUNTS:{Colors.END}")
        if not bounded_accounts:
            print(f"   {Colors.YELLOW}● No third-party platforms are currently bound.{Colors.END}")
        else:
            for p_id in bounded_accounts:
                p_name = PLATFORM_MAP.get(p_id, f"Unknown ({p_id})")
                print(f"   {Colors.CYAN}●{Colors.END} {Colors.WHITE}{p_name}{Colors.END}")
                
        print("")
        
        print(f" {Colors.BLUE}⊛ AVAILABLE PLATFORMS:{Colors.END}")
        if not available_platforms:
            print(f"   {Colors.DIM}● None{Colors.END}")
        else:
            for p_id in available_platforms:
                p_name = PLATFORM_MAP.get(p_id, f"Unknown ({p_id})")
                print(f"   {Colors.DIM}● {p_name}{Colors.END}")
                
        print(f"\n{Colors.MAGENTA}●{'═' * 48}●{Colors.END}")
        
    except Exception as e:
        print_error(f"Error fetching platform info: {str(e)}")
        print_error(f"Raw response might be different: {response.text}")
        
    wait_for_enter()


def owner_details():
    draw_header("OWNER DETAILS")

    print(f" {Colors.DBLUE}{'─' * 46}{Colors.END}")
    print(f" {Colors.GOLD}{Colors.BOLD}DEVELOPER INFO{Colors.END}")
    print(f" {Colors.DBLUE}{'─' * 46}{Colors.END}")
    print(f" {Colors.TEAL}Dev Name{Colors.END}    {Colors.WHITE}EH MUNNA{Colors.END}")
    print(f" {Colors.TEAL}Version {Colors.END}    {Colors.GREEN}v2.0  Premium / Secure{Colors.END}")
    print(f" {Colors.TEAL}Platform{Colors.END}    {Colors.GRAY}Garena Free Fire{Colors.END}")
    print(f" {Colors.DBLUE}{'─' * 46}{Colors.END}")
    print(f" {Colors.GRAY}Built for fast, secure Garena bind management.{Colors.END}")
    print(f" {Colors.GRAY}Report any bugs directly on Telegram.{Colors.END}")
    print(f" {Colors.DBLUE}{'─' * 46}{Colors.END}")

    wait_for_enter()


def show_menu():
    draw_header()

    options = [
        ("01", "CHECK BIND INFO",       Colors.TEAL),
        ("02", "BIND EMAIL",            Colors.TEAL),
        ("03", "UNBIND EMAIL",          Colors.TEAL),
        ("04", "CHANGE BIND EMAIL",     Colors.TEAL),
        ("05", "CANCEL BIND REQUEST",   Colors.YELLOW),
        ("06", "EAT TO ACCESS TOKEN",   Colors.LBLUE),
        ("07", "REVOKE ACCESS TOKEN",   Colors.LBLUE),
        ("08", "GET LOGIN HISTORY",     Colors.LBLUE),
        ("09", "CHECK BOUND ACCOUNTS",  Colors.LBLUE),
        ("10", "ACCESS TOKEN TO JWT",   Colors.PINK),
        ("11", "OWNER DETAILS",         Colors.GRAY),
        ("12", "ACCESS TOKEN TO BAN",   Colors.RED),
    ]

    print(f" {Colors.GOLD}{Colors.BOLD}MENU{Colors.END}")
    print(f" {Colors.DBLUE}{'─' * 46}{Colors.END}")
    for num, label, col in options:
        print(f" {Colors.DBLUE}[{Colors.END}{Colors.GOLD}{Colors.BOLD}{num}{Colors.END}{Colors.DBLUE}]{Colors.END}  {col}{label}{Colors.END}")
    print(f" {Colors.DBLUE}[{Colors.END}{Colors.RED}{Colors.BOLD}00{Colors.END}{Colors.DBLUE}]{Colors.END}  {Colors.RED}EXIT{Colors.END}")
    print(f" {Colors.DBLUE}{'─' * 46}{Colors.END}")
    print()

def main():
    _dispatch = {
        "1":  bind_info,          "01": bind_info,
        "2":  bind_email,         "02": bind_email,
        "3":  unbind_email,       "03": unbind_email,
        "4":  change_bind_email,  "04": change_bind_email,
        "5":  cancel_bind,        "05": cancel_bind,
        "6":  eat_to_access_token,"06": eat_to_access_token,
        "7":  revoke_access_token,"07": revoke_access_token,
        "8":  login_history,      "08": login_history,
        "9":  check_bound_accounts,"09":check_bound_accounts,
        "10": access_to_jwt,
        "11": owner_details,
        "12": ban_account,
    }

    while True:
        show_menu()
        choice = input_prompt("Select Option").strip().lstrip("0") or "0"

        if choice in ("0", "00"):
            clear_screen()
            print(f"\n {Colors.GREEN}✔  Safely Exited. See you!{Colors.END}\n")
            sys.exit(0)

        fn = _dispatch.get(choice)
        if fn:
            fn()
        else:
            print(f"\n {Colors.RED}✘  Invalid option [{choice}]{Colors.END}\n")
            time.sleep(1.2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n {Colors.GREEN}✔  Exited cleanly.{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n {Colors.RED}✘  Fatal: {e}{Colors.END}")
        input(f" {Colors.GRAY}Press Enter to exit …{Colors.END}  ")