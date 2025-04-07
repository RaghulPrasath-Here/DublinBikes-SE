
from sqlalchemy import create_engine, text

############################# CONNECT TO THE DATABASE #######################################

connection_string = f"mysql+pymysql://{db.USER}:{db.PASSWORD}@{db.URI}:{db.PORT}/{db.DB}"
engine = create_engine(connection_string, echo=True)




