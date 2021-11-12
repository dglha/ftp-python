from ftplib import FTP

a = FTP('') # Put your server ip address here
a.login('ndphuc', 'phucpro')
print(a.pwd())
print(a.dir())