"Config for Gunicorn"
workers = 3              # number of workers Gunicorn will spawn 

bind = '0.0.0.0:443'  # this is where you declare on which address your 
                         # gunicorn app is running.
                         # Basically where Nginx will forward the request to