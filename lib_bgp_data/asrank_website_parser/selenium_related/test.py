import concurrent.futures

def double(num):
    return num * 3

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    doubles = {executor.submit(double, num): num for num in range(30)}
    print(type(doubles), len(doubles))
    print()
    for double in concurrent.futures.as_completed(doubles):
        try:
            data = double.result()
            print(data, doubles[double])
        except:
            print('nothing')
