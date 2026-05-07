from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

DATABASE_URL = "mysql+pymysql://root:admin@localhost/studio02" 

engine = create_engine(DATABASE_URL, echo=True)

# Esto crea una sesión única por cada hilo/petición de usuario
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()

# 2. Función para inicializar tablas
def init_db():
    Base.metadata.create_all(bind=engine)