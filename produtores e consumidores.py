import threading
import numpy as np
import time


requests  = set(np.arange(0,1000))
responses = set()

condition = threading.Condition()

def handle_requests():
    global running
    threads = []

    for _ in range(4):
        consumer_thread = threading.Thread(target=consumidora)
        consumer_thread.start()
        threads.append(consumer_thread)

    while requests:
        p_threads = []
        with condition:
            for request in requests:
                # Create a new thread to process the request
                producer_thread = threading.Thread(target=produtora,args=(request,))
                p_threads.append(producer_thread)
                threads.append(producer_thread)

        for thread in p_threads:
            thread.start()
            thread.join()


    with condition:
        condition.notify_all()

    for thread in threads:
        thread.join()

def produtora(request):
    global responses

    request = request * 10000
    with condition:
        responses.add(request)
        condition.notify()
        print("Sended ",request)

def consumidora():
    global requests,responses,running
    while((requests)):
         with condition:
            condition.wait()  # Wait until notified by the producer
            if(not requests):
                break
        
            item = responses.pop()
            response = int(item/10000)
            print("Recieved ",response)
            try:
                requests.remove(response)
            except:
                pass
    return None

# Start the thread to handle requests
thread = threading.Thread(target=handle_requests)
thread.start()
thread.join()
print("All requests processed.")
