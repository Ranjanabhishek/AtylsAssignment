import redis
"""
   - Singleton design pattern to manage redis connection
   - there will be single connection for entire application 
   - for every redis call we will not create new connection again & again and it will reduce overhead on redis cluster
   - connection will be re-new after every deployment
"""
class RedisConnection:
    _instance = None

    def __new__(cls, host='localhost', port=6379, db=0):
        if not cls._instance:
            cls._instance = super(RedisConnection, cls).__new__(cls)
            cls._instance.create_connection(host, port, db)
        return cls._instance
    
    def create_connection(self, host, port, db):
        try:
            self.connection = redis.Redis(host=host, port=port, db=db)
            self.connection.ping()
            print("Connected to Redis...")
        except redis.ConnectionError as e:
            print(f"failed to connect to Redis.... {e}")
            self.connection = None

    def get_connection(self):
        return self.connection

