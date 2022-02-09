# получим объект файла
from posixpath import split


accountsFile = open("Accounts.txt", "r")

loginsFile = open('logins.txt', 'w')
passwordsFile = open('passwords.txt', 'w')

lines = accountsFile.readlines()

# итерация по строкам
for line in lines:
    if line.find('@') < 0:
        continue
    else:
        data = line.split(':')
        loginsFile.write(data[0] + '\n')
        passwordsFile.write(data[1])


# закрываем файл
accountsFile.close()
loginsFile.close()
passwordsFile.close()
