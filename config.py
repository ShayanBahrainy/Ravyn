"Config for Gunicorn"
workers = 3              # number of workers Gunicorn will spawn 

bind = '0.0.0.0:443'  # this is where you declare on which address your 
                         # gunicorn app is running.
                         # Basically where Nginx will forward the request to

pidfile = '/var/run/gunicorn/ravyn.pid' # create a simple pid file for gunicorn. 

user = 'opc'          # the user gunicorn will run on

daemon = False          # this is only to tell gunicorn to deamonize the server process

errorlog = 'gunicorn/error-ravyn.log'    # error log

accesslog = 'gunicorn/access-ravyn.log'  # access log

proc_name = 'gunicorn-ravyn'            # the gunicorn process name