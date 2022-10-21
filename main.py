import datetime
import io
import json
import psutil
import requests
import subprocess
import time
import zipfile

# Loads the install_update module, which makes sure all required libraries are installed to their required versions.
from install_update import *        

# Makes sure an authentication file exists.
if not os.path.exists("auth.json") or not os.path.getsize("auth.json"):
    print("Authentication file not found. Generating empty template...")
    d = {
        "prefix": "~",
        "slash_commands": False,
        "webserver_address": "0.0.0.0",
        "webserver_port": "",
        "discord_token": "",
        "owner_id": [],
        "rapidapi_key": "",
        "rapidapi_secret": "",
        "alexflipnote_key": "",
        "giphy_key": "",
    }
    with open("auth.json", "w", encoding="utf-8") as f:
        json.dump(d, f, indent=4)
    input("auth.json generated. Please fill in discord_token and restart bot when done.")
    raise SystemExit


ffmpeg = "./ffmpeg"
print("Verifying FFmpeg installation...")

if os.name == "nt":
    try:
        os.system("color")
    except:
        traceback.print_exc()
    with requests.get("https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip", stream=True) as resp:
        try:
            v = resp.url.rsplit("/", 1)[-1].split("-", 1)[-1].rsplit(".", 1)[0].split("-", 1)[0]
            r = subprocess.run(ffmpeg, stderr=subprocess.PIPE)
            s = r.stderr[:r.stderr.index(b"\n")].decode("utf-8", "replace").strip().lower()
            if s.startswith("ffmpeg"):
                s = s[6:].lstrip()
            if s.startswith("version"):
                s = s[7:].lstrip()
            s = s.split("-", 1)[0]
            if s != v:
                print(f"FFmpeg version outdated ({v} > {s})")
                raise FileNotFoundError
            print(f"FFmpeg version {s} found; skipping installation...")
        except FileNotFoundError:
            print(f"Downloading FFmpeg version {v}...")
            subprocess.run([sys.executable, "downloader.py", "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip", "ffmpeg.zip"], cwd="misc")
            print("Download complete; extracting new FFmpeg installation...")
            f = "misc/ffmpeg.zip"
            with zipfile.ZipFile(f) as z:
                names = [name for name in z.namelist() if "/bin/" in name and ".exe" in name]
                for i, name in enumerate(names):
                    print(f"{i}/{len(names)}")
                    fn = name.rsplit("/", 1)[-1]
                    with open(fn, "wb") as y:
                        with z.open(name, "r") as x:
                            while True:
                                b = x.read(1048576)
                                if not b:
                                    break
                                y.write(b)
            print("FFmpeg extraction complete.")
            os.remove(f)
    # if os.path.exists("misc"):
    #     if not os.path.exists("misc/ffmpeg-c"):
    #         print("Downloading ffmpeg version 4.2.2...")
    #         os.mkdir("misc/ffmpeg-c")
    #         subprocess.run([sys.executable, "downloader.py", "https://dl.dropboxusercontent.com/s/6vjpswpkxubnig4/ffmpeg-c.zip?dl=1", "ffmpeg-c.zip"], cwd="misc")
    #         print("Download complete; extracting new FFmpeg installation...")
    #         f = "misc/ffmpeg-c.zip"
    #         with zipfile.ZipFile(f) as z:
    #             z.extractall("misc/ffmpeg-c")
    #         print("FFmpeg extraction complete.")
    #         os.remove(f)
    if not os.path.exists("misc/poppler"):
        print("Downloading Poppler version 21.10.0...")
        os.mkdir("misc/poppler")
        subprocess.run([sys.executable, "downloader.py", "https://cdn.discordapp.com/attachments/731709481863479436/899556463016554496/Poppler.zip", "poppler.zip"], cwd="misc")
        print("Download complete; extracting new Poppler installation...")
        f = "misc/poppler.zip"
        with zipfile.ZipFile(f) as z:
            z.extractall("misc/poppler")
        print("Poppler extraction complete.")
        os.remove(f)
else:
    try:
        subprocess.run(ffmpeg)
    except FileNotFoundError:
        print(f"Downloading FFmpeg...")
        subprocess.run(("wget", "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"))
        print("Download complete; extracting new FFmpeg installation...")
        os.mkdir(".temp")
        subprocess.run(("tar", "-xf", "ffmpeg-release-amd64-static.tar.xz", "-C", ".temp"))
        fi = os.listdir(".temp")[0]
        os.rename(f".temp/{fi}/ffmpeg", "ffmpeg")
        os.rename(f".temp/{fi}/ffprobe", "ffprobe")
        os.rename(f".temp/{fi}/qt-faststart", "qt-faststart")
        subprocess.run(("rm", "-rf", ".temp"))


# Repeatedly attempts to delete a file, waiting 1 second between attempts.
def delete(f):
    while os.path.exists(f):
        try:
            os.remove(f)
            return
        except:
            traceback.print_exc()
        time.sleep(1)

sd = "shutdown.tmp"
rs = "restart.tmp"
hb = "heartbeat.tmp"
hb_ack = "heartbeat_ack.tmp"

delete(sd)
delete("log.txt")


# Main watchdog loop.
att = 0
while not os.path.exists(sd):
    delete(rs)
    delete(hb)
    proc = psutil.Popen([python, "bot.py"])
    start = time.time()
    print("Bot started with PID \033[1;34;40m" + str(proc.pid) + "\033[1;37;40m.")
    time.sleep(12)
    try:
        alive = True
        if proc.is_running():
            print("\033[1;32;40mHeartbeat started\033[1;37;40m.")
            while alive:
                if not os.path.exists(hb):
                    if os.path.exists(hb_ack):
                        os.rename(hb_ack, hb)
                    else:
                        with open(hb, "wb"):
                            pass
                print(
                    "\033[1;36;40m Heartbeat at "
                    + str(datetime.datetime.now())
                    + "\033[1;37;40m."
                )
                for i in range(32):
                    time.sleep(0.25)
                    ld = os.listdir()
                    if rs in ld or sd in ld:
                        alive = False
                        break
                if os.path.exists(hb):
                    break
            for child in proc.children(recursive=True):
                try:
                    child.terminate()
                    try:
                        child.wait(timeout=2)
                    except psutil.TimeoutExpired:
                        child.kill()
                except:
                    traceback.print_exc()
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except psutil.TimeoutExpired:
                    proc.kill()
            except psutil.NoSuchProcess:
                pass
            if os.path.exists(sd):
                break
        if time.time() - start < 60:
            att += 1
        else:
            att = 0
        if att > 16:
            print("\033[1;31;40mBot crashed 16 times in a row. Waiting 5 minutes before trying again.\033[1;37;40m")
            time.sleep(300)
            att = 0
        if alive:
            print("\033[1;31;40mBot failed to acknowledge heartbeat signal, restarting...\033[1;37;40m")
        else:
            print("\033[1;31;40mBot sent restart signal, advancing...\033[1;37;40m")
    except KeyboardInterrupt:
        raise
    except:
        traceback.print_exc()
    time.sleep(0.5)

if proc.is_running():
    try:
        for child in proc.children():
            child.terminate()
            try:
                child.wait(timeout=2)
            except psutil.TimeoutExpired:
                child.kill()
    except:
        traceback.print_exc()
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except psutil.TimeoutExpired:
        proc.kill()

delete(sd)
delete(rs)
delete(hb)
delete(hb_ack)

print("Shutdown signal confirmed. Program will now terminate. ")
raise SystemExit