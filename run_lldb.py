import pexpect
import time
import subprocess
import sys

child = pexpect.spawn('lldb /Volumes/External/Code/aot/build_fast/Source/www/SynanDaemon/SynanDaemon', encoding='utf-8')
child.logfile = sys.stdout
child.expect(r'\(lldb\)')
child.sendline('b abort')
child.expect(r'\(lldb\)')
child.sendline('env RML=/Volumes/External/Code/aot')
child.expect(r'\(lldb\)')
child.sendline('run --host 0.0.0.0 --port 8089')

# Wait for server to start fully
time.sleep(15)

# Send request
subprocess.run(['curl', '-s', '-X', 'POST', 'http://localhost:8089/?dummy=1&action=syntax&langua=Ukrainian', '-d', 'ст. 631'])

idx = child.expect([r'stopped', r'Segmentation fault', r'EXC_BAD_ACCESS', pexpect.EOF, pexpect.TIMEOUT], timeout=15)
if idx < 3:
    child.sendline('bt 100')
    child.expect(r'\(lldb\)')
    child.sendline('quit')
    child.expect(pexpect.EOF)
else:
    print("\n=== No crash detected ===\n")
