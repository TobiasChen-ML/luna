import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('185.207.207.200', username='root', password='Roxygirl020888$')

cmd = (
    "redis-cli DEL user:balance:telegram_2050741746 "
    "user:balance:telegram_8598574739 "
    "auth:checkin:telegram_2050741746:20260504 "
    "auth:checkin:telegram_8598574739:20260504"
)
stdin, stdout, stderr = client.exec_command(cmd)
print('DELETED:', stdout.read().decode())

# Verify keys are gone
cmd2 = "redis-cli KEYS '*telegram_2050741746*'; redis-cli KEYS '*telegram_8598574739*'"
stdin2, stdout2, stderr2 = client.exec_command(cmd2)
print('REMAINING KEYS:', stdout2.read().decode())

client.close()
