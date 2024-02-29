from amqpstorm import management

HOST_NAME = "localhost"

if __name__ == '__main__':
    # If using a self-signed certificate, change verify=True to point at your CA bundle.
    # You can disable certificate verification for testing by passing in verify=False.
    #API = management.ManagementApi('https://rmq.amqpstorm.io:15671', 'guest',
    API = management.ManagementApi('http://43.203.101.26:15671')#, 'admin', 'rabbit_password', verify=False)

    print('List all queues.')
    for queue in API.queue.list():
        print('%s: %s' % (queue.get('name'), queue.get('messages')))
    print('')

    #print('List all queues containing the keyword: amqpstorm.')
    #for queue in API.queue.list(name='amqpstorm'):
    #    print('%s: %s' % (queue.get('name'), queue.get('messages')))
    #print('')

    #print('List all queues using regex that starts with: amqpstorm.')
    #for queue in API.queue.list(name='^amqpstorm', use_regex=True):
    #    print('%s: %s' % (queue.get('name'), queue.get('messages')))
