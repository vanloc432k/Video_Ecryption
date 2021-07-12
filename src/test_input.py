while True:
    print('Reset!')
    name = input().strip()
    if(name == 'exit'):
        break
    print(name.split(' ').remove(''))
    print('Hello', name)