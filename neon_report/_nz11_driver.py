# -*- coding: utf-8 -*-
try:
    import psycopg2
    print('psycopg2', psycopg2.__version__)
except Exception as e:
    print('no psycopg2:', e)
try:
    import psycopg
    print('psycopg3', psycopg.__version__)
except Exception as e:
    print('no psycopg3:', e)
try:
    import pg8000
    print('pg8000', pg8000.__version__)
except Exception as e:
    print('no pg8000:', e)
